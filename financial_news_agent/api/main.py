"""FastAPI application initialization."""

from __future__ import annotations

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from ..config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Financial News Agent API",
    description="AI agent for financial news analysis with multi-turn conversations",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.on_event("startup")
async def startup_event() -> None:
    """Run on application startup."""
    logger.info("Starting Financial News Agent API")
    logger.info(f"CORS origins: {settings.cors_origins_list}")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Run on application shutdown."""
    logger.info("Shutting down Financial News Agent API")
