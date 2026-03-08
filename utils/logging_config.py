# MCP Foundry for Trading — Logging Configuration
# Created for the MCP Foundry project

"""
Logging Configuration
======================

Provides a consistent, structured logging setup for the entire project.
Call ``setup_logging()`` once at application startup.
"""

from __future__ import annotations

import logging
import os
import sys


def setup_logging(
    level: str | None = None,
    log_file: str | None = None,
) -> None:
    """
    Configure logging for the MCP Foundry.

    Args:
        level: Log level as a string (e.g., ``"DEBUG"``, ``"INFO"``).
               Defaults to the ``LOG_LEVEL`` environment variable, or ``"INFO"``.
        log_file: Optional path to a log file. If provided, logs are written
                  to both the console and the file.
    """
    level = level or os.getenv("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
    ]

    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=numeric_level,
        format=fmt,
        datefmt=datefmt,
        handlers=handlers,
        force=True,
    )

    # Quiet down noisy third-party loggers
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging initialised — level=%s file=%s", level, log_file or "(console only)"
    )
