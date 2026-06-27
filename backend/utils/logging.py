import logging
import sys
from pathlib import Path
from backend.config import settings

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "newsmind.log"

# Define log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logger(name: str) -> logging.Logger:
    """
    Sets up a logger with console and file handlers.
    """
    logger = logging.getLogger(name)

    # Set log level based on configuration
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    logger.setLevel(level)

    # Avoid duplicate handlers if setup is called multiple times
    if logger.hasHandlers():
        return logger

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)

    # File Handler
    try:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to initialize file logger: {e}", file=sys.stderr)

    return logger
