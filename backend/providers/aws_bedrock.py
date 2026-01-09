"""AWS Bedrock pricing provider."""

import asyncio
import logging
import re
from datetime import datetime

import httpx

from models import ModelPricing, Pricing, BatchPricing
from .base import BaseProvider
from .registry import ProviderRegistry

logger = logging.getLogger(__name__)

# AWS Pricing API endpoints (public, no auth required)
BEDROCK_URL = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/us-east-1/index.json"
BEDROCK_FM_URL = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/us-east-1/index.json"


class AWSBedrockProvider(BaseProvider):
    """Provider for AWS Bedrock pricing data."""

    name = "aws_bedrock"
    display_name = "AWS Bedrock"

    async def fetch(self) -> list[ModelPricing]:
        """Fetch pricing from both Bedrock sources."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Fetch both sources concurrently
            bedrock_resp, fm_resp = await asyncio.gather(
                client.get(BEDROCK_URL),
                client.get(BEDROCK_FM_URL),
            )
            bedrock_resp.raise_for_status()
            fm_resp.raise_for_status()

            bedrock_data = bedrock_resp.json()
            fm_data = fm_resp.json()

        models: dict[str, ModelPricing] = {}

        # Parse AmazonBedrock data
        self._parse_bedrock_data(bedrock_data, models)

        # Parse AmazonBedrockFoundationModels data
        self._parse_fm_data(fm_data, models)

        return list(models.values())

    def _parse_bedrock_data(
        self, data: dict, models: dict[str, ModelPricing]
    ) -> None:
        """Parse AmazonBedrock pricing data."""
        products = data.get("products", {})
        terms = data.get("terms", {}).get("OnDemand", {})

        for sku, product in products.items():
            attrs = product.get("attributes", {})
            model_name = attrs.get("model", "")
            if not model_name:
                continue

            # Skip non-model products (Guardrails, etc.)
            usage_type = attrs.get("usagetype", "")
            if "Guardrail" in usage_type or "CustomModel" in usage_type:
                continue

            # Get price
            term_data = terms.get(sku)
            if not term_data:
                continue

            term = list(term_data.values())[0]
            price_dim = list(term["priceDimensions"].values())[0]
            price_usd = float(price_dim["pricePerUnit"].get("USD", "0"))
            description = price_dim.get("description", "")

            # Determine price type from description/usagetype
            is_input = "input" in usage_type.lower() or "input" in description.lower()
            is_output = "output" in usage_type.lower() or "output" in description.lower()
            is_batch = "batch" in usage_type.lower() or "batch" in description.lower()

            # Create or update model
            model_id = self._normalize_model_id(model_name)
            full_id = f"{self.name}:{model_id}"

            if full_id not in models:
                models[full_id] = ModelPricing(
                    id=full_id,
                    provider=self.name,
                    model_id=model_id,
                    model_name=model_name,
                    pricing=Pricing(),
                    batch_pricing=None,
                    capabilities=["text"],
                    last_updated=datetime.now(),
                )

            model = models[full_id]

            # Update prices
            if is_batch:
                if model.batch_pricing is None:
                    model.batch_pricing = BatchPricing()
                if is_input:
                    model.batch_pricing.input = price_usd
                elif is_output:
                    model.batch_pricing.output = price_usd
            else:
                if is_input:
                    model.pricing.input = price_usd
                elif is_output:
                    model.pricing.output = price_usd

    def _parse_fm_data(
        self, data: dict, models: dict[str, ModelPricing]
    ) -> None:
        """Parse AmazonBedrockFoundationModels pricing data."""
        products = data.get("products", {})
        terms = data.get("terms", {}).get("OnDemand", {})

        for sku, product in products.items():
            attrs = product.get("attributes", {})
            service_name = attrs.get("servicename", "")
            if not service_name:
                continue

            # Extract model name from service name
            # e.g., "Claude 3.5 Sonnet (Amazon Bedrock Edition)" -> "Claude 3.5 Sonnet"
            model_name = re.sub(r"\s*\(Amazon Bedrock Edition\)\s*$", "", service_name)

            usage_type = attrs.get("usagetype", "")

            # Get price
            term_data = terms.get(sku)
            if not term_data:
                continue

            term = list(term_data.values())[0]
            price_dim = list(term["priceDimensions"].values())[0]
            price_usd = float(price_dim["pricePerUnit"].get("USD", "0"))
            description = price_dim.get("description", "")

            # Determine price type
            is_input = "Input" in usage_type
            is_output = "Output" in usage_type or "Response" in description
            is_batch = "batch" in usage_type.lower() or "Batch" in description
            is_cache_read = "CacheRead" in usage_type or "Cache Read" in description
            is_cache_write = "CacheWrite" in usage_type or "Cache Write" in description

            # Skip provisioned throughput and other non-token pricing
            if "ProvisionedThroughput" in usage_type:
                continue

            # Create or update model
            model_id = self._normalize_model_id(model_name)
            full_id = f"{self.name}:{model_id}"

            if full_id not in models:
                # Detect capabilities from model name
                capabilities = ["text"]
                name_lower = model_name.lower()
                if any(x in name_lower for x in ["vision", "vl", "image", "stable"]):
                    capabilities.append("vision")
                if any(x in name_lower for x in ["audio", "sonic", "voxtral"]):
                    capabilities.append("audio")
                if "embed" in name_lower:
                    capabilities = ["embedding"]

                models[full_id] = ModelPricing(
                    id=full_id,
                    provider=self.name,
                    model_id=model_id,
                    model_name=model_name,
                    pricing=Pricing(),
                    batch_pricing=None,
                    capabilities=capabilities,
                    last_updated=datetime.now(),
                )

            model = models[full_id]

            # Update prices based on type
            if is_batch:
                if model.batch_pricing is None:
                    model.batch_pricing = BatchPricing()
                if is_input:
                    model.batch_pricing.input = price_usd
                elif is_output:
                    model.batch_pricing.output = price_usd
            elif is_cache_read:
                model.pricing.cached_input = price_usd
            elif is_cache_write:
                model.pricing.cached_write = price_usd
            elif is_input and not is_cache_read and not is_cache_write:
                # Only set if not already set (prefer standard over latency optimized)
                if model.pricing.input is None:
                    model.pricing.input = price_usd
            elif is_output:
                if model.pricing.output is None:
                    model.pricing.output = price_usd

    def _normalize_model_id(self, name: str) -> str:
        """Normalize model name to ID format."""
        # Lowercase, replace spaces with hyphens, remove special chars
        model_id = name.lower()
        model_id = re.sub(r"[^a-z0-9\s\-\.]", "", model_id)
        model_id = re.sub(r"\s+", "-", model_id)
        return model_id


# Register provider
ProviderRegistry.register(AWSBedrockProvider())
