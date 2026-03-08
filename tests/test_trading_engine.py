# MCP Foundry for Trading — Tests: Trading Engine
# Created for the MCP Foundry project

"""
Tests for the exchange-agnostic TradingEngine.

All tests use the ``mock_connector`` fixture so we never hit a real exchange.
"""

from __future__ import annotations

import pytest

from core.trading_engine import TradingEngine


@pytest.fixture
def engine(mock_connector):
    return TradingEngine(mock_connector)


class TestMarketOrders:
    """Test market order convenience methods."""

    @pytest.mark.asyncio
    async def test_market_buy(self, engine, mock_connector) -> None:
        await engine.execute_market_buy("BTCUSDT", qty=0.001)
        mock_connector.place_order.assert_called_once()
        spec = mock_connector.place_order.call_args[0][0]
        assert spec.side == "buy"
        assert spec.order_type == "market"
        assert spec.qty == 0.001

    @pytest.mark.asyncio
    async def test_market_sell(self, engine, mock_connector) -> None:
        await engine.execute_market_sell("BTCUSDT", qty=0.002)
        spec = mock_connector.place_order.call_args[0][0]
        assert spec.side == "sell"
        assert spec.qty == 0.002

    @pytest.mark.asyncio
    async def test_market_buy_with_tp_sl(self, engine, mock_connector) -> None:
        await engine.execute_market_buy(
            "BTCUSDT", qty=0.001, take_profit=70000.0, stop_loss=65000.0
        )
        spec = mock_connector.place_order.call_args[0][0]
        assert spec.take_profit == 70000.0
        assert spec.stop_loss == 65000.0


class TestLimitOrders:
    """Test limit order placement."""

    @pytest.mark.asyncio
    async def test_limit_buy(self, engine, mock_connector) -> None:
        await engine.execute_limit_order(
            "BTCUSDT", side="buy", qty=0.01, price=66000.0
        )
        spec = mock_connector.place_order.call_args[0][0]
        assert spec.order_type == "limit"
        assert spec.price == 66000.0
        assert spec.time_in_force == "gtc"


class TestPositionManagement:
    """Test position management methods."""

    @pytest.mark.asyncio
    async def test_close_position(self, engine, mock_connector) -> None:
        result = await engine.close_position("BTCUSDT")
        assert result is not None
        spec = mock_connector.place_order.call_args[0][0]
        assert spec.side == "sell"  # Closes a long position
        assert spec.reduce_only is True

    @pytest.mark.asyncio
    async def test_close_no_position(self, engine, mock_connector) -> None:
        mock_connector.get_positions.return_value = []
        result = await engine.close_position("BTCUSDT")
        assert result is None

    @pytest.mark.asyncio
    async def test_cancel_all_orders(self, engine, mock_connector) -> None:
        results = await engine.cancel_all_orders()
        assert isinstance(results, list)


class TestMarketIntelligence:
    """Test market data convenience methods."""

    @pytest.mark.asyncio
    async def test_get_current_price(self, engine) -> None:
        price = await engine.get_current_price("BTCUSDT")
        assert price == 67500.0

    @pytest.mark.asyncio
    async def test_get_account_summary(self, engine) -> None:
        summary = await engine.get_account_summary()
        assert "total_equity" in summary
        assert "open_positions" in summary
        assert summary["total_equity"] == 10000.0

    @pytest.mark.asyncio
    async def test_get_market_snapshot(self, engine) -> None:
        snapshot = await engine.get_market_snapshot("BTCUSDT")
        assert snapshot["symbol"] == "BTCUSDT"
        assert "last_price" in snapshot
        assert "recent_candles" in snapshot
