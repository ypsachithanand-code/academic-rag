import logging
import sys
from typing import Optional
from app.core.config import settings


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """Configures centralized logging for the application.

    Args:
        level: Optional log level string (DEBUG, INFO, WARNING, ERROR).
               Defaults to DEBUG if settings.DEBUG is True, else INFO.

    Returns:
        Configured logger instance.
    """
    if level is None:
        log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    else:
        log_level = getattr(logging, level.upper(), logging.INFO)

    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )

    formatter = logging.Formatter(fmt=log_format, datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    logger = logging.getLogger("academic_rag")
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        logger.addHandler(console_handler)

    logger.propagate = False
    return logger


logger = setup_logging()
