# MCP Foundry for Trading — Trading Engine
# Created for the MCP Foundry project
#
# This module demonstrates how to build trading logic that depends ONLY on the
# UTI — no exchange-specific imports, no vendor lock-in. Swap the connector
# and the same strategy works on any exchange.

"""
Trading Engine
===============

A lightweight, exchange-agnostic trading engine built on top of the Universal
Trading Interface. It coordinates order placement, position tracking, and
basic strategy execution through the UTI contract.

This engine is intentionally simple — it's meant to be a clear starting point
that you can extend with your own strategies. We kept it readable rather than
clever, because we think good infrastructure should be easy to understand.

**Usage:**

.. code-block:: python

    from core.trading_engine import TradingEngine
    from connectors.bybit import BybitConnector

    connector = BybitConnector(api_key="...", api_secret="...", testnet=True)
    engine = TradingEngine(connector)

    await engine.execute_market_buy("BTCUSDT", qty=0.001)
"""

from __future__ import annotations

import logging
from typing import Any

from core.exceptions import (
    UTIError,
)
from core.interface import (
    OrderResponse,
    OrderSpec,
    UniversalTradingInterface,
)

logger = logging.getLogger(__name__)


class TradingEngine:
    """
    Exchange-agnostic trading engine.

    The engine holds a reference to any UTI-compatible connector and exposes
    higher-level convenience methods for common trading workflows.

    Args:
        connector: Any object implementing the ``UniversalTradingInterface``.
    """

    def __init__(self, connector: UniversalTradingInterface) -> None:
        self.connector = connector
        logger.info("TradingEngine initialised with %s", type(connector).__name__)

    # ------------------------------------------------------------------
    # Convenience — Order Placement
    # ------------------------------------------------------------------

    async def execute_market_buy(
        self,
        symbol: str,
        qty: float,
        take_profit: float | None = None,
        stop_loss: float | None = None,
    ) -> OrderResponse:
        """
        Place a market buy order with optional TP/SL.

        Args:
            symbol: Trading pair (e.g., ``"BTCUSDT"``).
            qty: Quantity in base asset units.
            take_profit: Optional take-profit price.
            stop_loss: Optional stop-loss price.

        Returns:
            The ``OrderResponse`` from the exchange.
        """
        spec = OrderSpec(
            symbol=symbol,
            side="buy",
            qty=qty,
            order_type="market",
            take_profit=take_profit,
            stop_loss=stop_loss,
        )
        logger.info("Market BUY — %s qty=%s tp=%s sl=%s", symbol, qty, take_profit, stop_loss)
        return await self.connector.place_order(spec)

    async def execute_market_sell(
        self,
        symbol: str,
        qty: float,
        take_profit: float | None = None,
        stop_loss: float | None = None,
    ) -> OrderResponse:
        """
        Place a market sell order with optional TP/SL.

        Args:
            symbol: Trading pair.
            qty: Quantity in base asset units.
            take_profit: Optional take-profit price.
            stop_loss: Optional stop-loss price.

        Returns:
            The ``OrderResponse`` from the exchange.
        """
        spec = OrderSpec(
            symbol=symbol,
            side="sell",
            qty=qty,
            order_type="market",
            take_profit=take_profit,
            stop_loss=stop_loss,
        )
        logger.info("Market SELL — %s qty=%s tp=%s sl=%s", symbol, qty, take_profit, stop_loss)
        return await self.connector.place_order(spec)

    async def execute_limit_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        price: float,
        time_in_force: str = "gtc",
        take_profit: float | None = None,
        stop_loss: float | None = None,
    ) -> OrderResponse:
        """
        Place a limit order.

        Args:
            symbol: Trading pair.
            side: ``"buy"`` or ``"sell"``.
            qty: Quantity in base asset units.
            price: Limit price.
            time_in_force: Time-in-force policy (default ``"gtc"``).
            take_profit: Optional take-profit price.
            stop_loss: Optional stop-loss price.

        Returns:
            The ``OrderResponse`` from the exchange.
        """
        spec = OrderSpec(
            symbol=symbol,
            side=side,
            qty=qty,
            order_type="limit",
            price=price,
            time_in_force=time_in_force,
            take_profit=take_profit,
            stop_loss=stop_loss,
        )
        logger.info(
            "Limit %s — %s qty=%s price=%s tif=%s",
            side.upper(), symbol, qty, price, time_in_force,
        )
        return await self.connector.place_order(spec)

    # ------------------------------------------------------------------
    # Convenience — Position Management
    # ------------------------------------------------------------------

    async def close_position(self, symbol: str) -> OrderResponse | None:
        """
        Close the entire open position for a symbol by placing a reduce-only
        market order in the opposite direction.

        Args:
            symbol: Trading pair.

        Returns:
            The ``OrderResponse`` if a position was closed, or ``None`` if
            there was no open position.
        """
        positions = await self.connector.get_positions(symbol=symbol)
        if not positions:
            logger.info("No open position for %s — nothing to close.", symbol)
            return None

        pos = positions[0]
        close_side = "sell" if pos.side == "long" else "buy"
        spec = OrderSpec(
            symbol=symbol,
            side=close_side,
            qty=pos.size,
            order_type="market",
            reduce_only=True,
        )
        logger.info("Closing %s position on %s — size=%s", pos.side, symbol, pos.size)
        return await self.connector.place_order(spec)

    async def cancel_all_orders(self, symbol: str | None = None) -> list[OrderResponse]:
        """
        Cancel all open orders, optionally filtered by symbol.

        Returns:
            A list of ``OrderResponse`` objects for each cancelled order.
        """
        open_orders = await self.connector.get_open_orders(symbol=symbol)
        results = []
        for order in open_orders:
            try:
                resp = await self.connector.cancel_order(order.symbol, order.order_id)
                results.append(resp)
            except UTIError as exc:
                logger.warning("Failed to cancel order %s: %s", order.order_id, exc)
        logger.info("Cancelled %d / %d open orders.", len(results), len(open_orders))
        return results

    # ------------------------------------------------------------------
    # Convenience — Market Intelligence
    # ------------------------------------------------------------------

    async def get_current_price(self, symbol: str) -> float:
        """Return the last traded price for a symbol."""
        ticker = await self.connector.get_ticker(symbol)
        return ticker.last_price

    async def get_account_summary(self) -> dict[str, Any]:
        """
        Return a concise account summary including balance and all open
        positions.
        """
        balance = await self.connector.get_wallet_balance()
        positions = await self.connector.get_positions()
        return {
            "total_equity": balance.total_equity,
            "available_balance": balance.available_balance,
            "currency": balance.currency,
            "open_positions": [
                {
                    "symbol": p.symbol,
                    "side": p.side,
                    "size": p.size,
                    "entry_price": p.entry_price,
                    "unrealised_pnl": p.unrealised_pnl,
                }
                for p in positions
            ],
        }

    async def get_market_snapshot(self, symbol: str) -> dict[str, Any]:
        """
        Return a quick market snapshot: ticker, best bid/ask, and recent
        candles.
        """
        ticker = await self.connector.get_ticker(symbol)
        candles = await self.connector.get_candles(symbol, interval="5m", limit=12)
        return {
            "symbol": ticker.symbol,
            "last_price": ticker.last_price,
            "bid": ticker.bid,
            "ask": ticker.ask,
            "high_24h": ticker.high_24h,
            "low_24h": ticker.low_24h,
            "volume_24h": ticker.volume_24h,
            "recent_candles": [
                {"t": c.timestamp, "o": c.open, "h": c.high, "l": c.low, "c": c.close, "v": c.volume}
                for c in candles[-5:]
            ],
        }
