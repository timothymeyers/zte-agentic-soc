"""
FastAPI application for the Agentic SOC MVP.

This module provides REST API endpoints for human interaction with the system,
including approval workflows, feedback submission, and hunting queries.
"""

from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.shared.logging import get_logger, configure_logging
from src.shared.metrics import get_metrics_registry


logger = get_logger(__name__)


# API Models
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str


class ReadinessResponse(BaseModel):
    """Readiness check response."""
    ready: bool
    services: Dict[str, str]


class MetricsResponse(BaseModel):
    """Metrics response."""
    metrics: Dict[str, Any]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown tasks.
    """
    # Startup
    logger.info("Starting Agentic SOC API")
    configure_logging()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Agentic SOC API")


# Create FastAPI application
app = FastAPI(
    title="Agentic SOC API",
    description="API for AI-powered Security Operations Center",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Agentic SOC API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        HealthResponse: Health status
    """
    from datetime import datetime
    
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness check endpoint.
    
    Returns:
        ReadinessResponse: Readiness status
    """
    # TODO: Check actual service dependencies
    services = {
        "cosmos_db": "ready",
        "sentinel": "ready",
        "defender": "ready"
    }
    
    all_ready = all(status == "ready" for status in services.values())
    
    return ReadinessResponse(
        ready=all_ready,
        services=services
    )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """
    Get application metrics.
    
    Returns:
        MetricsResponse: Application metrics
    """
    registry = get_metrics_registry()
    metrics = registry.get_all_metrics()
    
    return MetricsResponse(metrics=metrics)


# Import route modules (will be created later)
# from src.api.routes import approval, feedback, hunting
# app.include_router(approval.router, prefix="/api/v1", tags=["approval"])
# app.include_router(feedback.router, prefix="/api/v1", tags=["feedback"])
# app.include_router(hunting.router, prefix="/api/v1", tags=["hunting"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
