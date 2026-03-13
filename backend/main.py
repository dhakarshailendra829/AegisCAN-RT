"""
FastAPI application factory and configuration.

Main entry point for the AegisCAN-RT backend.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.config import settings
from backend.routers import gateway, analytics, external
from backend.dependencies import engine
from core.logger_engine import logger as core_logger
from core.metrics_engine import metrics_engine
from src.gateway import Gateway

# Configure logging
logger = logging.getLogger(__name__)


# Global gateway instance
_gateway_instance: Gateway = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.

    Startup:
    - Create database tables
    - Start metrics collection
    - Initialize gateway

    Shutdown:
    - Stop metrics collection
    - Stop gateway
    - Clean up resources
    """
    # ========================================================================
    # Startup Events
    # ========================================================================
    try:
        logger.info("🚀 Starting AegisCAN-RT Application")

        # Import here to avoid circular imports
        from sqlalchemy import text

        # Test database connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")

        # Create tables
        try:
            from backend.models import Base  # Import after engine created
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ Database tables initialized")
        except ImportError:
            logger.warning("⚠️ backend.models not found, skipping table creation")

        # Start metrics collection
        metrics_engine.start()
        logger.info("✅ Metrics engine started")

        logger.info("🎉 Application startup complete")

        yield

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise

    finally:
        # ========================================================================
        # Shutdown Events
        # ========================================================================
        try:
            logger.info("🛑 Shutting down AegisCAN-RT Application")

            # Stop metrics
            await metrics_engine.stop()
            logger.info("✅ Metrics engine stopped")

            # Dispose engine
            await engine.dispose()
            logger.info("✅ Database connection closed")

            logger.info("✅ Graceful shutdown complete")

        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title="AegisCAN-RT API",
    description="Deterministic ultra-low-latency BLE→CAN real-time gateway for safety-critical automotive systems",
    version="4.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)

# ============================================================================
# Router Configuration
# ============================================================================

# Include API routers
app.include_router(
    gateway.router,
    prefix="/api/gateway",
    tags=["Gateway Control"],
    responses={
        400: {"description": "Bad Request"},
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"},
    },
)

app.include_router(
    analytics.router,
    prefix="/api/analytics",
    tags=["Analytics"],
    responses={
        400: {"description": "Bad Request"},
        500: {"description": "Internal Server Error"},
    },
)

app.include_router(
    external.router,
    prefix="/api/external",
    tags=["External Data"],
    responses={
        400: {"description": "Bad Request"},
        500: {"description": "Internal Server Error"},
    },
)

# ============================================================================
# Health Check Endpoints
# ============================================================================


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Basic health check endpoint.

    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "4.0.0",
        "debug": settings.DEBUG,
    }


@app.get("/status", tags=["Health"])
async def status_check():
    """
    Detailed status check endpoint.

    Returns:
        dict: System status information
    """
    return {
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "version": "4.0.0",
        "debug": settings.DEBUG,
        "database": {
            "type": "sqlite" if settings.is_sqlite else "postgresql" if settings.is_postgresql else "mysql",
            "url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL,
        },
        "logging": {
            "level": settings.LOG_LEVEL,
        },
    }


# ============================================================================
# Error Handlers
# ============================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "status": "error",
        "message": "Internal server error",
        "detail": str(exc) if settings.DEBUG else "An error occurred",
    }


# ============================================================================
# Main Entry Point
# ============================================================================


def create_app():
    """
    Application factory function.

    Returns:
        FastAPI: Configured FastAPI application
    """
    return app


if __name__ == "__main__":
    logger.info(f"🚀 Starting uvicorn on {settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )