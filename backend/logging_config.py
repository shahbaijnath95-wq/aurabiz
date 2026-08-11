"""Structured logging configuration using loguru."""

import sys
from loguru import logger


def setup_logging():
    """Configure loguru for the application."""
    logger.remove()  # Remove default handler

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        format=log_format,
        level="INFO",
        colorize=True,
    )

    logger.add(
        sys.stderr,
        format=log_format,
        level="ERROR",
        colorize=True,
    )

    # File logging for production
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="gz",
    )

    return logger
