#!/usr/bin/env python3
# MCP Foundry for Trading — Example: AI Agent Integration
# Created for the MCP Foundry project
#
# This is the killer demo — it shows how ANY AI agent can trade through
# the MCP Foundry server using simple HTTP calls.

"""
Example: AI Agent Integration
===============================

This example demonstrates how an AI agent can use the MCP Foundry to:

1. Discover available trading tools
2. Analyse market conditions
3. Make a trading decision
4. Execute the trade with risk management

The agent communicates with the MCP server over HTTP — no exchange-specific
SDK needed. This means the same agent code works whether the server is
connected to Bybit, Binance, or any future connector.

**Prerequisites:**

1. Start the MCP server::

    export EXCHANGE_API_KEY="your_key"
    export EXCHANGE_API_SECRET="your_secret"
    export EXCHANGE_TESTNET="true"
    python scripts/run_server.py

2. Install the OpenAI client (optional, for the LLM-powered agent)::

    pip install openai

3. Run this example::

    python examples/ai_agent_integration.py

The example works in two modes:

- **Without an LLM** (default): A simple rule-based agent that demonstrates
  the integration pattern.
- **With an LLM**: Uncomment the LLM section to see how GPT/Claude can
  drive trading decisions through the MCP Foundry.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp

SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")


class SimpleRuleBasedAgent:
    """
    A minimal rule-based trading agent that uses the MCP Foundry.

    This demonstrates the integration pattern. In production, you'd replace
    the decision logic with an LLM, a quantitative model, or any other
    strategy — the MCP interface stays the same.
    """

    def __init__(self, server_url: str) -> None:
        self.server_url = server_url
        self.session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def discover_tools(self) -> list:
        """Step 1: Ask the MCP server what tools are available."""
        session = await self._get_session()
        async with session.get(f"{self.server_url}/tools") as resp:
            return await resp.json()

    async def analyse_market(self, symbol: str) -> dict:
        """Step 2: Gather market data to inform a decision."""
        session = await self._get_session()
        async with session.get(f"{self.server_url}/market/snapshot/{symbol}") as resp:
            return await resp.json()

    async def check_account(self) -> dict:
        """Step 3: Check account status before trading."""
        session = await self._get_session()
        async with session.get(f"{self.server_url}/account/summary") as resp:
            return await resp.json()

    async def make_decision(self, market_data: dict, account: dict) -> dict | None:
        """
        Step 4: Decide whether to trade.

        This is where your strategy lives. Replace this with an LLM call,
        a quantitative model, or any decision framework you prefer.
        """
        market_data.get("last_price", 0)
        candles = market_data.get("recent_candles", [])

        if len(candles) < 2:
            print("  Not enough data to make a decision.")
            return None

        # Simple momentum check: is the price trending up?
        recent_close = candles[-1].get("c", 0)
        previous_close = candles[-2].get("c", 0)

        if recent_close > previous_close:
            print(f"  Momentum is UP ({previous_close} -> {recent_close})")
            return {
                "action": "buy",
                "symbol": market_data["symbol"],
                "qty": 0.001,
                "reason": "Positive short-term momentum",
            }
        else:
            print(f"  Momentum is DOWN ({previous_close} -> {recent_close})")
            print("  Holding — no trade.")
            return None

    async def execute_trade(self, decision: dict) -> dict:
        """Step 5: Execute the trade through the MCP server."""
        session = await self._get_session()
        order = {
            "symbol": decision["symbol"],
            "side": decision["action"],
            "qty": decision["qty"],
            "order_type": "market",
        }
        async with session.post(f"{self.server_url}/trade/place_order", json=order) as resp:
            return await resp.json()

    async def run(self, symbol: str = "BTCUSDT") -> None:
        """Run the full agent loop once."""
        print(f"\n{'='*60}")
        print("  MCP Foundry — AI Agent Demo")
        print(f"  Symbol: {symbol}")
        print(f"{'='*60}\n")

        # Step 1: Discover tools
        print("[1/5] Discovering available tools...")
        tools = await self.discover_tools()
        print(f"  Found {len(tools)} tools: {[t['name'] for t in tools]}\n")

        # Step 2: Analyse market
        print(f"[2/5] Analysing market for {symbol}...")
        market = await self.analyse_market(symbol)
        print(f"  Last price: {market.get('last_price')}")
        print(f"  24h range: {market.get('low_24h')} — {market.get('high_24h')}\n")

        # Step 3: Check account
        print("[3/5] Checking account status...")
        account = await self.check_account()
        print(f"  Equity: {account.get('total_equity')}")
        print(f"  Open positions: {len(account.get('open_positions', []))}\n")

        # Step 4: Make decision
        print("[4/5] Making trading decision...")
        decision = await self.make_decision(market, account)

        if decision is None:
            print("\n[5/5] No trade executed. Agent cycle complete.\n")
            return

        print(f"  Decision: {decision['action'].upper()} {decision['qty']} {decision['symbol']}")
        print(f"  Reason: {decision['reason']}\n")

        # Step 5: Execute (commented out for safety — uncomment to go live)
        print("[5/5] Trade execution (disabled in demo mode)")
        print("  To enable, uncomment the execute_trade call in the source.\n")
        # result = await self.execute_trade(decision)
        # print(f"  Result: {result}")

        print("Agent cycle complete.\n")

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()


# ---------------------------------------------------------------------------
# LLM-Powered Agent (Optional)
# ---------------------------------------------------------------------------
# Uncomment the section below to use an LLM (e.g., GPT-4) as the decision
# engine. The LLM receives market data and account info, then returns a
# structured trading decision.
#
# async def llm_decision(market_data: dict, account: dict) -> dict | None:
#     """Use an LLM to make a trading decision based on market data."""
#     from openai import AsyncOpenAI
#
#     client = AsyncOpenAI()
#
#     prompt = f"""You are a trading assistant. Based on the following data,
#     decide whether to buy, sell, or hold.
#
#     Market Data:
#     {json.dumps(market_data, indent=2)}
#
#     Account:
#     {json.dumps(account, indent=2)}
#
#     Respond with JSON: {{"action": "buy"|"sell"|"hold", "qty": float, "reason": "..."}}
#     If holding, set action to "hold".
#     """
#
#     response = await client.chat.completions.create(
#         model="gpt-4.1-mini",
#         messages=[{"role": "user", "content": prompt}],
#         response_format={"type": "json_object"},
#     )
#
#     result = json.loads(response.choices[0].message.content)
#     if result.get("action") == "hold":
#         return None
#     return result


async def main() -> None:
    agent = SimpleRuleBasedAgent(SERVER_URL)
    try:
        await agent.run("BTCUSDT")
    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
