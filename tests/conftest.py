# MCP Foundry for Trading — Test Fixtures
# Created for the MCP Foundry project

"""
Shared pytest fixtures for the MCP Foundry test suite.

These fixtures provide mock connectors and sample data that any test module
can use. If you're writing tests for a new connector, the ``mock_connector``
fixture is a good starting point.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from core.interface import (
    BalanceData,
    CandleData,
    OrderBookData,
    OrderBookEntry,
    OrderResponse,
    PositionData,
    TickerData,
)


@pytest.fixture
def sample_ticker() -> TickerData:
    """A realistic BTC/USDT ticker snapshot."""
    return TickerData(
        symbol="BTCUSDT",
        last_price=67500.0,
        bid=67499.5,
        ask=67500.5,
        high_24h=68200.0,
        low_24h=66800.0,
        volume_24h=12345.67,
        timestamp=1700000000000,
    )


@pytest.fixture
def sample_balance() -> BalanceData:
    """A realistic account balance."""
    return BalanceData(
        total_equity=10000.0,
        available_balance=8500.0,
        currency="USDT",
        assets=[
            {
                "currency": "USDT",
                "equity": 10000.0,
                "available": 8500.0,
                "wallet_balance": 10000.0,
                "unrealised_pnl": 0.0,
            }
        ],
    )


@pytest.fixture
def sample_position() -> PositionData:
    """A realistic open long position."""
    return PositionData(
        symbol="BTCUSDT",
        side="long",
        size=0.01,
        entry_price=67000.0,
        mark_price=67500.0,
        unrealised_pnl=5.0,
        leverage=10,
        liquidation_price=60000.0,
    )


@pytest.fixture
def sample_order_response() -> OrderResponse:
    """A realistic order response."""
    return OrderResponse(
        order_id="test-order-001",
        symbol="BTCUSDT",
        side="buy",
        order_type="market",
        qty=0.001,
        filled_qty=0.001,
        avg_fill_price=67500.0,
        status="filled",
        timestamp=1700000000000,
    )


@pytest.fixture
def sample_candles() -> list[CandleData]:
    """A small set of candle data for testing."""
    base_ts = 1700000000000
    return [
        CandleData(timestamp=base_ts + i * 60000, open=67000 + i * 10, high=67050 + i * 10, low=66950 + i * 10, close=67020 + i * 10, volume=100.0 + i)
        for i in range(5)
    ]


@pytest.fixture
def mock_connector(
    sample_ticker, sample_balance, sample_position, sample_order_response, sample_candles
) -> AsyncMock:
    """
    A fully mocked UTI connector.

    All methods return realistic sample data. Use this fixture when you want
    to test logic that depends on a connector without hitting a real exchange.
    """
    connector = AsyncMock()
    connector.ping.return_value = True
    connector.get_ticker.return_value = sample_ticker
    connector.get_wallet_balance.return_value = sample_balance
    connector.get_positions.return_value = [sample_position]
    connector.get_open_orders.return_value = []
    connector.place_order.return_value = sample_order_response
    connector.cancel_order.return_value = OrderResponse(
        order_id="test-order-001",
        symbol="BTCUSDT",
        side="buy",
        order_type="market",
        qty=0.001,
        status="cancelled",
    )
    connector.get_order.return_value = sample_order_response
    connector.get_candles.return_value = sample_candles
    connector.get_orderbook.return_value = OrderBookData(
        symbol="BTCUSDT",
        bids=[OrderBookEntry(price=67499.5, qty=1.5), OrderBookEntry(price=67499.0, qty=2.0)],
        asks=[OrderBookEntry(price=67500.5, qty=1.0), OrderBookEntry(price=67501.0, qty=3.0)],
    )
    connector.get_exchange_info.return_value = {"category": "linear", "symbols": []}
    return connector
