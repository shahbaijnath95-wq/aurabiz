"""Structured logging configuration using loguru."""

import sys
import os
from pathlib import Path
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

    # File logging for production — use AppData (C:\Program Files is read-only!)
    appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    log_dir = Path(appdata) / "AuraBiz" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        str(log_dir / "app_{time:YYYY-MM-DD}.log"),
        format=log_format,
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="gz",
    )

    return logger
