# MCP Foundry for Trading — Connector Registry
# Created for the MCP Foundry project

"""
Connector Registry
===================

This module provides a simple registry for discovering and loading UTI
connectors at runtime. When you add a new connector, register it here so
that the MCP server and CLI tools can find it automatically.

**Adding a new connector:**

1. Create ``connectors/your_exchange.py`` implementing the UTI.
2. Import and register it in this file.
3. That's it — the MCP server will pick it up.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, type[Any]] = {}


def register_connector(name: str, cls: type[Any]) -> None:
    """
    Register a connector class under a human-readable name.

    Args:
        name: Lowercase exchange name (e.g., ``"bybit"``).
        cls: The connector class that implements the UTI.
    """
    _REGISTRY[name.lower()] = cls


def get_connector(name: str) -> type[Any]:
    """
    Look up a registered connector by name.

    Args:
        name: Lowercase exchange name.

    Returns:
        The connector class.

    Raises:
        KeyError: If no connector is registered under that name.
    """
    try:
        return _REGISTRY[name.lower()]
    except KeyError:
        available = ", ".join(sorted(_REGISTRY.keys())) or "(none)"
        raise KeyError(
            f"No connector registered for '{name}'. Available: {available}"
        ) from None


def list_connectors() -> dict[str, type[Any]]:
    """Return a copy of the full connector registry."""
    return dict(_REGISTRY)


# ---------------------------------------------------------------------------
# Auto-register built-in connectors
# ---------------------------------------------------------------------------

from connectors.bybit import BybitConnector  # noqa: E402

register_connector("bybit", BybitConnector)

__all__ = [
    "register_connector",
    "get_connector",
    "list_connectors",
    "BybitConnector",
]
