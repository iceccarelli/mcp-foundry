# MCP Foundry for Trading — Configuration Loader
# Created for the MCP Foundry project

"""
Configuration Loader
=====================

Loads configuration from environment variables and optional YAML files.
Environment variables always take precedence over file-based config.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_config(
    config_path: str | None = None,
) -> dict[str, Any]:
    """
    Load and merge configuration from a YAML file and environment variables.

    Priority (highest to lowest):

    1. Environment variables (prefixed with ``MCP_`` or ``EXCHANGE_``).
    2. YAML config file (if provided).
    3. Built-in defaults.

    Args:
        config_path: Optional path to a YAML configuration file.

    Returns:
        A merged configuration dictionary.
    """
    config: dict[str, Any] = {
        "exchange": "bybit",
        "testnet": True,
        "api_key": "",
        "api_secret": "",
        "category": "linear",
        "server_host": "0.0.0.0",
        "server_port": 8000,
        "log_level": "INFO",
        "risk": {
            "max_risk_per_trade_pct": 2.0,
            "max_position_size_pct": 10.0,
            "max_total_exposure_pct": 50.0,
            "max_open_positions": 5,
            "max_daily_loss_pct": 5.0,
            "min_balance_reserve": 100.0,
        },
    }

    # Layer 1: YAML file
    if config_path:
        path = Path(config_path)
        if path.exists():
            try:
                import yaml

                with open(path) as f:
                    file_config = yaml.safe_load(f) or {}
                _deep_merge(config, file_config)
                logger.info("Loaded config from %s", config_path)
            except ImportError:
                logger.warning(
                    "PyYAML not installed — skipping YAML config. "
                    "Install with: pip install pyyaml"
                )
        else:
            logger.warning("Config file not found: %s", config_path)

    # Layer 2: Environment variables (override everything)
    env_map = {
        "MCP_EXCHANGE": "exchange",
        "EXCHANGE_TESTNET": "testnet",
        "EXCHANGE_API_KEY": "api_key",
        "EXCHANGE_API_SECRET": "api_secret",
        "EXCHANGE_CATEGORY": "category",
        "MCP_SERVER_HOST": "server_host",
        "MCP_SERVER_PORT": "server_port",
        "LOG_LEVEL": "log_level",
    }

    for env_var, config_key in env_map.items():
        value = os.getenv(env_var)
        if value is not None:
            # Type coercion
            if config_key == "testnet":
                config[config_key] = value.lower() in ("true", "1", "yes")
            elif config_key == "server_port":
                config[config_key] = int(value)
            else:
                config[config_key] = value

    return config


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    """Recursively merge ``override`` into ``base`` in place."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
