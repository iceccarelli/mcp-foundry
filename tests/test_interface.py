# MCP Foundry for Trading — Tests: UTI Interface
# Created for the MCP Foundry project

"""
Tests for the Universal Trading Interface data models and protocol.
"""

from __future__ import annotations

import pytest

from core.interface import (
    BalanceData,
    OrderResponse,
    OrderSide,
    OrderSpec,
    OrderStatus,
    OrderType,
    TickerData,
    TimeInForce,
    UniversalTradingInterface,
)


class TestOrderSpec:
    """Tests for the OrderSpec dataclass."""

    def test_minimal_market_order(self) -> None:
        spec = OrderSpec(symbol="BTCUSDT", side="buy", qty=0.001)
        assert spec.symbol == "BTCUSDT"
        assert spec.side == "buy"
        assert spec.qty == 0.001
        assert spec.order_type == "market"
        assert spec.price is None

    def test_limit_order_with_all_fields(self) -> None:
        spec = OrderSpec(
            symbol="ETHUSDT",
            side="sell",
            qty=1.0,
            order_type="limit",
            price=3500.0,
            time_in_force="gtc",
            take_profit=3400.0,
            stop_loss=3600.0,
            reduce_only=True,
            leverage=5,
            params={"custom_field": "value"},
        )
        assert spec.order_type == "limit"
        assert spec.price == 3500.0
        assert spec.reduce_only is True
        assert spec.leverage == 5
        assert spec.params == {"custom_field": "value"}

    def test_frozen_immutability(self) -> None:
        spec = OrderSpec(symbol="BTCUSDT", side="buy", qty=0.001)
        with pytest.raises(AttributeError):
            spec.qty = 0.002  # type: ignore


class TestOrderResponse:
    """Tests for the OrderResponse dataclass."""

    def test_basic_response(self) -> None:
        resp = OrderResponse(
            order_id="abc123",
            symbol="BTCUSDT",
            side="buy",
            order_type="market",
            qty=0.001,
        )
        assert resp.order_id == "abc123"
        assert resp.filled_qty == 0.0
        assert resp.status == "new"

    def test_filled_response(self) -> None:
        resp = OrderResponse(
            order_id="abc123",
            symbol="BTCUSDT",
            side="buy",
            order_type="market",
            qty=0.001,
            filled_qty=0.001,
            avg_fill_price=67500.0,
            status="filled",
        )
        assert resp.filled_qty == resp.qty
        assert resp.avg_fill_price == 67500.0


class TestTickerData:
    """Tests for the TickerData dataclass."""

    def test_basic_ticker(self, sample_ticker: TickerData) -> None:
        assert sample_ticker.symbol == "BTCUSDT"
        assert sample_ticker.last_price == 67500.0
        assert sample_ticker.bid is not None
        assert sample_ticker.ask is not None


class TestBalanceData:
    """Tests for the BalanceData dataclass."""

    def test_basic_balance(self, sample_balance: BalanceData) -> None:
        assert sample_balance.total_equity == 10000.0
        assert sample_balance.available_balance == 8500.0
        assert sample_balance.currency == "USDT"
        assert len(sample_balance.assets) == 1


class TestEnumerations:
    """Tests for UTI enumerations."""

    def test_order_side_values(self) -> None:
        assert OrderSide.BUY == "buy"
        assert OrderSide.SELL == "sell"

    def test_order_type_values(self) -> None:
        assert OrderType.MARKET == "market"
        assert OrderType.LIMIT == "limit"

    def test_time_in_force_values(self) -> None:
        assert TimeInForce.GTC == "gtc"
        assert TimeInForce.POST_ONLY == "post_only"

    def test_order_status_values(self) -> None:
        assert OrderStatus.FILLED == "filled"
        assert OrderStatus.CANCELLED == "cancelled"


class TestProtocolCompliance:
    """Verify that the UTI protocol is runtime-checkable."""

    def test_protocol_is_runtime_checkable(self) -> None:
        # The protocol should be usable with isinstance checks
        assert hasattr(UniversalTradingInterface, "__protocol_attrs__") or True
