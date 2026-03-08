# MCP Foundry for Trading — Core Module
# Created for the MCP Foundry project
# https://github.com/mcp-foundry/mcp-foundry

"""
Core module of the MCP Foundry for Trading.

This package contains the foundational building blocks of the Universal
Trading Interface (UTI):

- ``interface``: The UTI protocol specification and data models.
- ``exceptions``: Standard exception hierarchy for all trading operations.
- ``trading_engine``: Exchange-agnostic trading engine built on the UTI.
- ``risk_management``: Exchange-agnostic risk management framework.
- ``mcp_server``: MCP-compatible server exposing UTI methods to AI agents.
"""

from core.exceptions import (
    AuthenticationError,
    ConnectionError,
    ExchangeError,
    InsufficientFundsError,
    InvalidOrderError,
    OrderNotFoundError,
    RateLimitError,
    UTIError,
)
from core.interface import (
    BalanceData,
    CandleData,
    OrderBookData,
    OrderBookEntry,
    OrderResponse,
    OrderSpec,
    PositionData,
    TickerData,
    UniversalTradingInterface,
)

__all__ = [
    "UniversalTradingInterface",
    "OrderSpec",
    "OrderResponse",
    "TickerData",
    "BalanceData",
    "PositionData",
    "CandleData",
    "OrderBookEntry",
    "OrderBookData",
    "UTIError",
    "ConnectionError",
    "AuthenticationError",
    "InsufficientFundsError",
    "OrderNotFoundError",
    "InvalidOrderError",
    "RateLimitError",
    "ExchangeError",
]
