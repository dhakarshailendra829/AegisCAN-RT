import logging
import logging.config
import os
from pathlib import Path
from backend.config import settings  

class LoggerEngine:
    def __init__(self, log_file: str = "data/system.log"):
        self.log_file = Path(log_file)
        self._configure()

    def _configure(self):
        log_dir = self.log_file.parent
        log_dir.mkdir(parents=True, exist_ok=True)

        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": settings.LOG_LEVEL,
                    "formatter": "standard",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "standard",
                    "filename": str(self.log_file),
                    "maxBytes": 10 * 1024 * 1024,  
                    "backupCount": 5,
                },
            },
            "root": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file"],
            },
        }

        logging.config.dictConfig(logging_config)
        self.logger = logging.getLogger("aegiscan")

    def debug(self, msg: str, extra: dict | None = None):
        self.logger.debug(msg, extra=extra)

    def info(self, msg: str, extra: dict | None = None):
        self.logger.info(msg, extra=extra)

    def warning(self, msg: str, extra: dict | None = None):
        self.logger.warning(msg, extra=extra)

    def error(self, msg: str, exc_info: bool = False, extra: dict | None = None):
        self.logger.error(msg, exc_info=exc_info, extra=extra)

    def critical(self, msg: str, extra: dict | None = None):
        self.logger.critical(msg, extra=extra)

logger_engine = LoggerEngine()
logger = logger_engine.logger  