from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class Pricing(BaseModel):
    input_tokens: float | None = None
    output_tokens: float | None = None
    cached_input_tokens: float | None = None
    reasoning_tokens: float | None = None
    image_input: float | None = None
    embedding: float | None = None


class Capabilities(BaseModel):
    text: bool | None = None
    vision: bool | None = None
    audio: bool | None = None
    embedding: bool | None = None
    image_generation: bool | None = None


ProviderType = Literal[
    "openrouter", "azure_openai", "aws_bedrock", "openai", "xai", "google_vertex"
]


class ModelPricing(BaseModel):
    id: str
    provider: ProviderType
    model_id: str
    model_name: str
    pricing: Pricing
    billing_mode: Literal["per_token", "per_image", "per_request"] = "per_token"
    currency: Literal["USD"] = "USD"
    capabilities: Capabilities | None = None
    context_length: int | None = None
    max_output_tokens: int | None = None
    source: Literal["api", "manual"]
    source_url: str | None = None
    last_updated: str
    last_verified: str | None = None
    notes: str | None = None


class UnifiedPricingDatabase(BaseModel):
    version: str
    last_sync: str
    models: list[ModelPricing]


class DisplayModel(BaseModel):
    provider_id: str
    provider_name: str
    model_id: str
    model_name: str
    cost_input: float | None = None
    cost_output: float | None = None
    cost_cache_read: float | None = None
    cost_reasoning: float | None = None
    context_limit: int | None = None
    output_limit: int | None = None
    input_modalities: list[str] | None = None
    output_modalities: list[str] | None = None
    last_updated: str | None = None
    source: Literal["api", "manual"] | None = None


class ProviderInfo(BaseModel):
    id: str
    name: str
    pricing_url: str | None = None
    api_url: str | None = None
    source: Literal["api", "manual"]


class ProviderWithModels(BaseModel):
    id: str
    name: str
    doc: str | None = None
    api: str | None = None
    model_count: int
    models: list[dict]


class SyncResult(BaseModel):
    provider: str
    success: bool
    models_count: int
    error: str | None = None


class ManualModel(BaseModel):
    model_id: str
    model_name: str
    pricing: Pricing
    billing_mode: Literal["per_token", "per_image", "per_request"] | None = None
    capabilities: Capabilities | None = None
    context_length: int | None = None
    notes: str | None = None


class ManualDataFile(BaseModel):
    provider: str
    source_url: str
    last_verified: str
    models: list[ManualModel]
