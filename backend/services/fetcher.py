"""Data fetch orchestrator."""

import logging
from datetime import datetime

from providers import ProviderRegistry
from .pricing import PricingService

logger = logging.getLogger(__name__)


class Fetcher:
    """Orchestrates fetching pricing data from all providers."""

    @classmethod
    async def refresh_all(cls) -> dict:
        """Refresh data from all providers."""
        logger.info("Starting full refresh...")
        start = datetime.now()

        models = await ProviderRegistry.fetch_all()
        PricingService.save_models(models)

        elapsed = (datetime.now() - start).total_seconds()
        logger.info(f"Refresh complete: {len(models)} models in {elapsed:.2f}s")

        return {
            "status": "ok",
            "models_count": len(models),
            "elapsed_seconds": elapsed,
            "timestamp": datetime.now().isoformat(),
        }

    @classmethod
    async def refresh_provider(cls, provider_name: str) -> dict:
        """Refresh data from a single provider."""
        logger.info(f"Refreshing provider: {provider_name}")
        start = datetime.now()

        models = await ProviderRegistry.fetch_provider(provider_name)
        PricingService.update_provider(provider_name, models)

        elapsed = (datetime.now() - start).total_seconds()
        logger.info(f"Provider {provider_name}: {len(models)} models in {elapsed:.2f}s")

        return {
            "status": "ok",
            "provider": provider_name,
            "models_count": len(models),
            "elapsed_seconds": elapsed,
            "timestamp": datetime.now().isoformat(),
        }
