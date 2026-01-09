"""Model Price Backend - FastAPI Application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from models import ModelPricing, ProviderInfo
from services import PricingService, Fetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: refresh data from all providers
    logger.info("Starting up - refreshing pricing data...")
    try:
        result = await Fetcher.refresh_all()
        logger.info(f"Startup refresh complete: {result['models_count']} models")
    except Exception as e:
        logger.error(f"Startup refresh failed: {e}")
    yield
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="Model Price API",
    description="API for AI model pricing comparison",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API root."""
    return {
        "message": "Welcome to Model Price API",
        "version": "0.2.0",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    stats = PricingService.get_stats()
    return {
        "status": "healthy",
        "models_count": stats["total_models"],
        "last_refresh": stats["last_refresh"],
    }


@app.get("/api/models", response_model=list[ModelPricing])
async def list_models(
    provider: str | None = Query(None, description="Filter by provider"),
    capability: str | None = Query(None, description="Filter by capability"),
    search: str | None = Query(None, description="Search model name"),
    sort_by: str = Query("model_name", description="Sort field"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
):
    """List all models with optional filters and sorting."""
    return PricingService.get_all(
        provider=provider,
        capability=capability,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@app.get("/api/models/{model_id:path}", response_model=ModelPricing)
async def get_model(model_id: str):
    """Get a single model by ID."""
    model = PricingService.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@app.get("/api/providers", response_model=list[ProviderInfo])
async def list_providers():
    """List all providers with stats."""
    return PricingService.get_providers()


@app.get("/api/stats")
async def get_stats():
    """Get overall statistics."""
    return PricingService.get_stats()


@app.post("/api/refresh")
async def refresh(provider: str | None = Query(None, description="Provider to refresh")):
    """Manually refresh pricing data."""
    try:
        if provider:
            result = await Fetcher.refresh_provider(provider)
        else:
            result = await Fetcher.refresh_all()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Refresh failed")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
