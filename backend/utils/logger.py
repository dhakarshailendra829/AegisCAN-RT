# backend/utils/logger.py
import logging
from backend.config import settings

# Configure root logger
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Main logger for the app
logger = logging.getLogger("aegiscan")

# Example usage: logger.info("Something happened")