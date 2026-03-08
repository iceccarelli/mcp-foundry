#!/usr/bin/env python3
# MCP Foundry for Trading — Example: Running the MCP Server
# Created for the MCP Foundry project
#
# This example shows how to start the MCP server and interact with it
# using simple HTTP requests.

"""
Example: Running the MCP Server
=================================

Demonstrates:
- Starting the MCP Foundry server
- Discovering available tools via the /tools endpoint
- Placing a trade via HTTP
- Querying account balance

**Step 1 — Start the server:**

.. code-block:: bash

    # Set your credentials
    export EXCHANGE_API_KEY="your_api_key"
    export EXCHANGE_API_SECRET="your_api_secret"
    export EXCHANGE_TESTNET="true"

    # Start the server
    python scripts/run_server.py

**Step 2 — Interact with curl (in another terminal):**

.. code-block:: bash

    # Discover available tools
    curl http://localhost:8000/tools | python -m json.tool

    # Get BTC price
    curl http://localhost:8000/market/ticker/BTCUSDT | python -m json.tool

    # Check your balance
    curl http://localhost:8000/account/balance | python -m json.tool

    # Place a market buy order
    curl -X POST http://localhost:8000/trade/place_order \\
      -H "Content-Type: application/json" \\
      -d '{"symbol": "BTCUSDT", "side": "buy", "qty": 0.001}' \\
      | python -m json.tool

    # Get account summary
    curl http://localhost:8000/account/summary | python -m json.tool

**Step 3 — Or use this Python script to do the same programmatically:**
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp

SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        # 1. Discover tools
        print("=== Available Tools ===")
        async with session.get(f"{SERVER_URL}/tools") as resp:
            tools = await resp.json()
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")

        # 2. Health check
        print("\n=== Health Check ===")
        async with session.get(f"{SERVER_URL}/health") as resp:
            health = await resp.json()
            print(f"  Status: {health['status']}, Connected: {health['connected']}")

        # 3. Get ticker
        print("\n=== BTC/USDT Ticker ===")
        async with session.get(f"{SERVER_URL}/market/ticker/BTCUSDT") as resp:
            ticker = await resp.json()
            print(f"  Last price: {ticker.get('last_price')}")

        # 4. Get balance
        print("\n=== Account Balance ===")
        async with session.get(f"{SERVER_URL}/account/balance") as resp:
            balance = await resp.json()
            print(f"  Equity: {balance.get('total_equity')} {balance.get('currency')}")

        # 5. Place a small order (uncomment to execute)
        # print("\n=== Placing Order ===")
        # order_data = {"symbol": "BTCUSDT", "side": "buy", "qty": 0.001}
        # async with session.post(f"{SERVER_URL}/trade/place_order", json=order_data) as resp:
        #     result = await resp.json()
        #     print(f"  Order: {result}")

        print("\nDone. The server is ready for your AI agent to connect.")


if __name__ == "__main__":
    asyncio.run(main())
