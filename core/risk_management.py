# MCP Foundry for Trading — Risk Management
# Created for the MCP Foundry project
#
# Exchange-agnostic risk management that works with any UTI connector.
# Swap the exchange — the risk rules stay the same.

"""
Risk Management
================

A configurable, exchange-agnostic risk management layer that sits between
your trading strategy and the UTI connector. It enforces position-sizing
rules, per-trade risk limits, and portfolio-level exposure caps before any
order reaches the exchange.

The goal is simple: protect your capital so you can keep trading. These
checks run locally and add negligible latency.

**Usage:**

.. code-block:: python

    from core.risk_management import RiskManager, RiskConfig
    from connectors.bybit import BybitConnector

    connector = BybitConnector(api_key="...", api_secret="...", testnet=True)
    risk = RiskManager(connector, RiskConfig(max_risk_per_trade_pct=1.0))

    # This will raise if the trade violates your risk rules
    await risk.validate_trade("BTCUSDT", side="buy", qty=0.01)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from core.exceptions import InvalidOrderError
from core.interface import UniversalTradingInterface

logger = logging.getLogger(__name__)


@dataclass
class RiskConfig:
    """
    Risk management configuration.

    Attributes:
        max_risk_per_trade_pct: Maximum percentage of total equity risked on
            a single trade (default 2.0%).
        max_position_size_pct: Maximum percentage of equity in a single
            position (default 10.0%).
        max_total_exposure_pct: Maximum total portfolio exposure as a
            percentage of equity (default 50.0%).
        max_open_positions: Maximum number of simultaneous open positions
            (default 5).
        max_daily_loss_pct: Maximum daily drawdown before trading is paused
            (default 5.0%).
        min_balance_reserve: Minimum balance that must remain untouched
            (default 100.0 in settlement currency).
    """
    max_risk_per_trade_pct: float = 2.0
    max_position_size_pct: float = 10.0
    max_total_exposure_pct: float = 50.0
    max_open_positions: int = 5
    max_daily_loss_pct: float = 5.0
    min_balance_reserve: float = 100.0


class RiskManager:
    """
    Exchange-agnostic risk manager.

    Validates proposed trades against a ``RiskConfig`` before they are sent
    to the exchange. All checks use live account data fetched through the UTI.

    Args:
        connector: Any UTI-compatible connector.
        config: A ``RiskConfig`` instance with your risk parameters.
    """

    def __init__(
        self,
        connector: UniversalTradingInterface,
        config: RiskConfig | None = None,
    ) -> None:
        self.connector = connector
        self.config = config or RiskConfig()
        self._daily_pnl: float = 0.0
        self._starting_equity: float | None = None
        logger.info("RiskManager initialised — config=%s", self.config)

    async def _ensure_starting_equity(self) -> None:
        """Lazily fetch starting equity on the first call of the day."""
        if self._starting_equity is None:
            balance = await self.connector.get_wallet_balance()
            self._starting_equity = balance.total_equity
            logger.info("Starting equity set to %.2f", self._starting_equity)

    # ------------------------------------------------------------------
    # Position Sizing
    # ------------------------------------------------------------------

    async def calculate_position_size(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        stop_loss_price: float,
    ) -> float:
        """
        Calculate the maximum position size based on per-trade risk.

        Uses the formula::

            risk_amount = equity * (max_risk_per_trade_pct / 100)
            position_size = risk_amount / abs(entry_price - stop_loss_price)

        Args:
            symbol: Trading pair.
            side: ``"buy"`` or ``"sell"``.
            entry_price: Expected entry price.
            stop_loss_price: Planned stop-loss price.

        Returns:
            Maximum quantity in base asset units.

        Raises:
            InvalidOrderError: If the stop-loss is on the wrong side of entry.
        """
        if side == "buy" and stop_loss_price >= entry_price:
            raise InvalidOrderError(
                message="Stop-loss must be below entry price for a buy order."
            )
        if side == "sell" and stop_loss_price <= entry_price:
            raise InvalidOrderError(
                message="Stop-loss must be above entry price for a sell order."
            )

        balance = await self.connector.get_wallet_balance()
        risk_amount = balance.total_equity * (self.config.max_risk_per_trade_pct / 100.0)
        price_distance = abs(entry_price - stop_loss_price)

        if price_distance == 0:
            raise InvalidOrderError(message="Entry and stop-loss prices cannot be equal.")

        size = risk_amount / price_distance
        logger.info(
            "Position size for %s %s: %.6f (risk_amount=%.2f, distance=%.2f)",
            side, symbol, size, risk_amount, price_distance,
        )
        return size

    # ------------------------------------------------------------------
    # Pre-Trade Validation
    # ------------------------------------------------------------------

    async def validate_trade(
        self,
        symbol: str,
        side: str,
        qty: float,
        price: float | None = None,
    ) -> bool:
        """
        Run all pre-trade risk checks. Raises ``InvalidOrderError`` if any
        check fails; returns ``True`` if the trade is acceptable.

        Checks performed:

        1. **Balance reserve** — Ensure minimum balance is maintained.
        2. **Position count** — Ensure we haven't exceeded max open positions.
        3. **Single-position exposure** — Ensure the trade doesn't exceed
           the per-position cap.
        4. **Total exposure** — Ensure aggregate exposure stays within limits.
        5. **Daily loss limit** — Ensure we haven't hit the daily drawdown cap.

        Args:
            symbol: Trading pair.
            side: ``"buy"`` or ``"sell"``.
            qty: Proposed quantity.
            price: Estimated fill price (if ``None``, fetched from ticker).

        Returns:
            ``True`` if all checks pass.

        Raises:
            InvalidOrderError: With a descriptive message if any check fails.
        """
        await self._ensure_starting_equity()

        balance = await self.connector.get_wallet_balance()
        positions = await self.connector.get_positions()

        # 1. Balance reserve
        if balance.available_balance < self.config.min_balance_reserve:
            raise InvalidOrderError(
                message=(
                    f"Available balance ({balance.available_balance:.2f}) is below "
                    f"the minimum reserve ({self.config.min_balance_reserve:.2f})."
                )
            )

        # 2. Position count
        if len(positions) >= self.config.max_open_positions:
            # Allow if we're adding to an existing position on the same symbol
            existing = [p for p in positions if p.symbol == symbol]
            if not existing:
                raise InvalidOrderError(
                    message=(
                        f"Maximum open positions ({self.config.max_open_positions}) reached. "
                        f"Close an existing position before opening a new one."
                    )
                )

        # 3. Single-position exposure
        if price is None:
            ticker = await self.connector.get_ticker(symbol)
            price = ticker.last_price

        trade_value = qty * price
        max_single = balance.total_equity * (self.config.max_position_size_pct / 100.0)
        if trade_value > max_single:
            raise InvalidOrderError(
                message=(
                    f"Trade value ({trade_value:.2f}) exceeds single-position limit "
                    f"({max_single:.2f} = {self.config.max_position_size_pct}% of equity)."
                )
            )

        # 4. Total exposure
        total_exposure = sum(p.size * (p.entry_price or 0) for p in positions) + trade_value
        max_total = balance.total_equity * (self.config.max_total_exposure_pct / 100.0)
        if total_exposure > max_total:
            raise InvalidOrderError(
                message=(
                    f"Total exposure ({total_exposure:.2f}) would exceed portfolio limit "
                    f"({max_total:.2f} = {self.config.max_total_exposure_pct}% of equity)."
                )
            )

        # 5. Daily loss limit
        if self._starting_equity and self._starting_equity > 0:
            current_drawdown_pct = (
                (self._starting_equity - balance.total_equity) / self._starting_equity
            ) * 100.0
            if current_drawdown_pct >= self.config.max_daily_loss_pct:
                raise InvalidOrderError(
                    message=(
                        f"Daily loss limit reached ({current_drawdown_pct:.2f}% drawdown, "
                        f"limit is {self.config.max_daily_loss_pct}%). Trading paused."
                    )
                )

        logger.info(
            "Trade validated — %s %s %s qty=%.6f price=%.2f",
            "PASS", side.upper(), symbol, qty, price,
        )
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def reset_daily_tracking(self) -> None:
        """
        Reset the daily PnL tracker. Call this at the start of each trading
        day or session.
        """
        self._starting_equity = None
        self._daily_pnl = 0.0
        logger.info("Daily risk tracking reset.")
