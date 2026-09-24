"""
NetSentry - Structured Logging
Configures application-wide logging with file rotation and console output.
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime


LOG_DIR = os.path.join(os.environ.get("APPDATA", "."), "NetSentry", "logs")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB per log file
BACKUP_COUNT = 3


def setup_logging(level: int = logging.INFO, console: bool = True) -> logging.Logger:
    """
    Configure application-wide logging.

    Args:
        level: Logging level (default: INFO)
        console: Whether to also log to console (default: True)

    Returns:
        The root 'netsentry' logger.
    """
    # Create log directory
    os.makedirs(LOG_DIR, exist_ok=True)

    # Create the root netsentry logger
    root_logger = logging.getLogger("netsentry")
    root_logger.setLevel(level)

    # Prevent duplicate handlers on re-init
    if root_logger.handlers:
        root_logger.handlers.clear()

    # File handler with rotation
    log_file = os.path.join(LOG_DIR, "netsentry.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root_logger.addHandler(file_handler)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        root_logger.addHandler(console_handler)

    root_logger.info(f"NetSentry logging initialized. Log file: {log_file}")

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under the netsentry namespace."""
    return logging.getLogger(f"netsentry.{name}")
