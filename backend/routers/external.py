"""
External data integration router.

Provides:
- Weather data integration (OpenWeather)
- Solar data integration (NASA POWER API)
- Environmental context for anomaly detection
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# API Endpoints
# ============================================================================

@router.get(
    "/weather",
    summary="Get weather data",
    responses={
        200: {"description": "Weather data retrieved"},
        503: {"description": "Weather service unavailable"},
        500: {"description": "Server error"}
    }
)
async def get_weather(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude")
):
    """
    Get weather data from OpenWeather API.

    Currently placeholder - requires OPENWEATHER_API_KEY configuration.

    Args:
        latitude: Location latitude
        longitude: Location longitude

    Returns:
        dict: Weather information
    """
    if not settings.OPENWEATHER_API_KEY:
        logger.warning("Weather API requested but OPENWEATHER_API_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weather service not configured"
        )

    try:
        logger.info(f"Weather request for coordinates: {latitude}, {longitude}")
        # Placeholder for actual OpenWeather API integration
        return {
            "status": "placeholder",
            "message": "Weather API integration pending",
            "location": {
                "latitude": latitude,
                "longitude": longitude
            }
        }

    except Exception as e:
        logger.error(f"Failed to retrieve weather data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve weather data"
        )


@router.get(
    "/solar",
    summary="Get solar irradiance data",
    responses={
        200: {"description": "Solar data retrieved"},
        503: {"description": "Solar service unavailable"},
        500: {"description": "Server error"}
    }
)
async def get_solar_data(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    start_date: str = Query(..., regex="^\\d{4}-\\d{2}-\\d{2}$", description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., regex="^\\d{4}-\\d{2}-\\d{2}$", description="End date (YYYY-MM-DD)")
):
    """
    Get solar irradiance data from NASA POWER API.

    Currently placeholder - provides integration point for solar data.

    Args:
        latitude: Location latitude
        longitude: Location longitude
        start_date: Start date for data retrieval
        end_date: End date for data retrieval

    Returns:
        dict: Solar irradiance data
    """
    try:
        logger.info(f"Solar data request for {latitude}, {longitude}: {start_date} to {end_date}")
        # Placeholder for actual NASA POWER API integration
        return {
            "status": "placeholder",
            "message": "NASA POWER API integration pending",
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "date_range": {
                "start": start_date,
                "end": end_date
            }
        }

    except Exception as e:
        logger.error(f"Failed to retrieve solar data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve solar data"
        )


@router.get(
    "/health",
    summary="Check external services health"
)
async def check_external_services():
    """
    Check health and configuration status of external services.

    Returns:
        dict: Service status information
    """
    return {
        "status": "healthy",
        "services": {
            "openweather": {
                "configured": bool(settings.OPENWEATHER_API_KEY),
                "base_url": "https://api.openweathermap.org"
            },
            "nasa_power": {
                "configured": True,
                "base_url": str(settings.NASA_POWER_API_BASE)
            }
        }
    }