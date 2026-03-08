# MCP Foundry for Trading — Tests: Risk Management
# Created for the MCP Foundry project

"""
Tests for the exchange-agnostic RiskManager.
"""

from __future__ import annotations

import pytest

from core.exceptions import InvalidOrderError
from core.interface import BalanceData, PositionData
from core.risk_management import RiskConfig, RiskManager


@pytest.fixture
def risk_config() -> RiskConfig:
    return RiskConfig(
        max_risk_per_trade_pct=2.0,
        max_position_size_pct=10.0,
        max_total_exposure_pct=50.0,
        max_open_positions=3,
        max_daily_loss_pct=5.0,
        min_balance_reserve=100.0,
    )


@pytest.fixture
def risk_manager(mock_connector, risk_config) -> RiskManager:
    return RiskManager(mock_connector, risk_config)


class TestPositionSizing:
    """Test position size calculation."""

    @pytest.mark.asyncio
    async def test_calculate_buy_position_size(self, risk_manager) -> None:
        size = await risk_manager.calculate_position_size(
            symbol="BTCUSDT", side="buy", entry_price=67500.0, stop_loss_price=67000.0
        )
        # equity=10000, risk=2% -> 200 / 500 = 0.4
        assert abs(size - 0.4) < 0.01

    @pytest.mark.asyncio
    async def test_invalid_stop_loss_for_buy(self, risk_manager) -> None:
        with pytest.raises(InvalidOrderError):
            await risk_manager.calculate_position_size(
                symbol="BTCUSDT", side="buy", entry_price=67500.0, stop_loss_price=68000.0
            )

    @pytest.mark.asyncio
    async def test_invalid_stop_loss_for_sell(self, risk_manager) -> None:
        with pytest.raises(InvalidOrderError):
            await risk_manager.calculate_position_size(
                symbol="BTCUSDT", side="sell", entry_price=67500.0, stop_loss_price=67000.0
            )


class TestTradeValidation:
    """Test pre-trade risk validation."""

    @pytest.mark.asyncio
    async def test_valid_trade_passes(self, risk_manager) -> None:
        result = await risk_manager.validate_trade(
            symbol="BTCUSDT", side="buy", qty=0.001, price=67500.0
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_insufficient_balance_reserve(self, risk_manager, mock_connector) -> None:
        mock_connector.get_wallet_balance.return_value = BalanceData(
            total_equity=50.0, available_balance=50.0, currency="USDT"
        )
        with pytest.raises(InvalidOrderError, match="minimum reserve"):
            await risk_manager.validate_trade(
                symbol="BTCUSDT", side="buy", qty=0.001, price=67500.0
            )

    @pytest.mark.asyncio
    async def test_max_positions_exceeded(self, risk_manager, mock_connector) -> None:
        # Create 3 positions on different symbols (max is 3)
        mock_connector.get_positions.return_value = [
            PositionData(symbol="BTCUSDT", side="long", size=0.01, entry_price=67000.0),
            PositionData(symbol="ETHUSDT", side="long", size=0.1, entry_price=3500.0),
            PositionData(symbol="SOLUSDT", side="long", size=1.0, entry_price=150.0),
        ]
        with pytest.raises(InvalidOrderError, match="Maximum open positions"):
            await risk_manager.validate_trade(
                symbol="DOGEUSDT", side="buy", qty=100, price=0.15
            )

    @pytest.mark.asyncio
    async def test_single_position_exposure_exceeded(self, risk_manager) -> None:
        # 10% of 10000 = 1000. qty=0.1 * 67500 = 6750 > 1000
        with pytest.raises(InvalidOrderError, match="single-position limit"):
            await risk_manager.validate_trade(
                symbol="BTCUSDT", side="buy", qty=0.1, price=67500.0
            )


class TestDailyTracking:
    """Test daily PnL tracking."""

    def test_reset_daily_tracking(self, risk_manager) -> None:
        risk_manager._starting_equity = 10000.0
        risk_manager._daily_pnl = -200.0
        risk_manager.reset_daily_tracking()
        assert risk_manager._starting_equity is None
        assert risk_manager._daily_pnl == 0.0
