#!/usr/bin/env python3
# MCP Foundry for Trading — Example: Basic Market Order
# Created for the MCP Foundry project
#
# This example shows how to use the UTI directly to place a market order
# on Bybit. It's the simplest possible integration — no MCP server needed.

"""
Example: Basic Market Order
============================

Demonstrates:
- Creating a BybitConnector
- Fetching the current price
- Placing a market buy order with take-profit and stop-loss
- Checking your balance afterwards

Before running, set your environment variables::

    export EXCHANGE_API_KEY="your_api_key"
    export EXCHANGE_API_SECRET="your_api_secret"

Then run::

    python examples/basic_market_order.py
"""

import asyncio
import os
import sys

# Ensure the project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.bybit import BybitConnector
from core.interface import OrderSpec
from utils.logging_config import setup_logging


async def main() -> None:
    setup_logging(level="INFO")

    # 1. Create a connector (testnet by default — safe for experimentation)
    connector = BybitConnector(
        api_key=os.getenv("EXCHANGE_API_KEY", ""),
        api_secret=os.getenv("EXCHANGE_API_SECRET", ""),
        testnet=True,
    )

    try:
        # 2. Check connectivity
        is_alive = await connector.ping()
        print(f"Exchange reachable: {is_alive}")

        # 3. Get the current price
        ticker = await connector.get_ticker("BTCUSDT")
        print(f"BTC/USDT last price: {ticker.last_price}")

        # 4. Check your balance
        balance = await connector.get_wallet_balance()
        print(f"Available balance: {balance.available_balance} {balance.currency}")

        # 5. Place a small market buy order (adjust qty for your account)
        spec = OrderSpec(
            symbol="BTCUSDT",
            side="buy",
            qty=0.001,
            order_type="market",
            take_profit=ticker.last_price * 1.02,  # 2% above entry
            stop_loss=ticker.last_price * 0.98,     # 2% below entry
        )
        print(f"\nPlacing order: {spec}")
        result = await connector.place_order(spec)
        print(f"Order placed — ID: {result.order_id}, Status: {result.status}")

        # 6. Check positions
        positions = await connector.get_positions(symbol="BTCUSDT")
        for pos in positions:
            print(f"Position: {pos.side} {pos.size} @ {pos.entry_price}")

    finally:
        await connector.close()


if __name__ == "__main__":
    asyncio.run(main())
