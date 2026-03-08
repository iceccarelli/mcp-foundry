# MCP Foundry for Trading

**The Universal Trading Interface — connecting AI agents to financial markets through one open standard.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()
[![UTI Version](https://img.shields.io/badge/UTI-v0.1.0-orange.svg)](docs/uti_specification.md)

---

## The Problem

Every AI agent that wants to trade needs custom integration code for every exchange. Every exchange has its own API, its own data formats, its own quirks. If you have **M** agents and **N** exchanges, you end up writing **M x N** integrations — and maintaining all of them.

This doesn't scale. It's the same problem USB solved for hardware peripherals, and the same problem that HTTP solved for networked applications.

## The Solution

The **Universal Trading Interface (UTI)** is an open standard that sits between AI agents and financial markets. Write your agent once, connect it to any exchange.

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│  AI Agent    │     │   MCP Foundry   │     │   Exchange   │
│  (Claude,    │────▶│   UTI Server    │────▶│   (Bybit,    │
│   GPT, etc.) │     │                 │     │    etc.)     │
└─────────────┘     └─────────────────┘     └──────────────┘
                           │
                    One interface.
                    Any agent.
                    Any exchange.
```

Instead of M x N integrations, you get **M + N** — each agent implements the UTI once, each exchange gets one connector, and everything just works.

## What's Included

| Component | Description |
| :--- | :--- |
| **`core/interface.py`** | The UTI specification — data models, enumerations, and the protocol contract |
| **`core/trading_engine.py`** | Exchange-agnostic trading engine with convenience methods |
| **`core/risk_management.py`** | Configurable pre-trade risk checks (position sizing, exposure limits, daily loss caps) |
| **`core/mcp_server.py`** | FastAPI server that exposes the UTI as a REST API for AI agents |
| **`connectors/bybit.py`** | Production-ready Bybit V5 connector — the reference implementation |
| **`enterprise/`** | Reserved for institutional add-ons (proprietary connectors, advanced algos) |
| **`gateway/`** | Reserved for the hosted gateway service (managed infrastructure) |
| **`examples/`** | Working examples: direct trading, MCP server usage, AI agent integration |
| **`tests/`** | Comprehensive test suite with mocked connectors |
| **`docs/`** | Architecture guides, UTI specification, and connector development guide |

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/mcp-foundry/mcp-foundry.git
cd mcp-foundry
pip install -e ".[dev]"
```

### 2. Configure your credentials

```bash
cp .env.example .env
# Edit .env with your exchange API credentials
```

### 3. Start the MCP server

```bash
python scripts/run_server.py
```

The server starts at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive API explorer.

### 4. Trade from any AI agent

```bash
# Discover available tools
curl http://localhost:8000/tools | python -m json.tool

# Get BTC price
curl http://localhost:8000/market/ticker/BTCUSDT

# Place an order
curl -X POST http://localhost:8000/trade/place_order \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "side": "buy", "qty": 0.001}'
```

### 5. Or use the UTI directly in Python

```python
import asyncio
from connectors.bybit import BybitConnector
from core.interface import OrderSpec

async def main():
    connector = BybitConnector(
        api_key="YOUR_KEY",
        api_secret="YOUR_SECRET",
        testnet=True,
    )
    ticker = await connector.get_ticker("BTCUSDT")
    print(f"BTC: {ticker.last_price}")

    spec = OrderSpec(symbol="BTCUSDT", side="buy", qty=0.001)
    order = await connector.place_order(spec)
    print(f"Order: {order.order_id}")

    await connector.close()

asyncio.run(main())
```

## Using Docker

```bash
# Build
docker build -t mcp-foundry .

# Run
docker run -p 8000:8000 \
  -e EXCHANGE_API_KEY=your_key \
  -e EXCHANGE_API_SECRET=your_secret \
  -e EXCHANGE_TESTNET=true \
  mcp-foundry
```

Or with Docker Compose:

```bash
docker-compose up
```

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=core --cov=connectors --cov-report=term-missing

# Specific module
pytest tests/test_trading_engine.py -v
```

## Architecture

The project follows a layered architecture designed for extensibility:

```
┌──────────────────────────────────────────────────┐
│                   AI Agents                       │
│          (Claude, GPT, LangChain, custom)         │
├──────────────────────────────────────────────────┤
│              MCP Server (REST API)                │
│         Tool discovery, authentication            │
├──────────────────────────────────────────────────┤
│         Trading Engine + Risk Manager             │
│    Strategy execution, position sizing, limits    │
├──────────────────────────────────────────────────┤
│          Universal Trading Interface              │
│     The contract — data models + protocol         │
├──────────────────────────────────────────────────┤
│              Exchange Connectors                  │
│        Bybit │ (your connector here)              │
└──────────────────────────────────────────────────┘
```

For a deeper dive, see [docs/architecture.md](docs/architecture.md).

## Building a New Connector

We designed the UTI to make adding new exchanges straightforward. The full guide is at [docs/connector_development_guide.md](docs/connector_development_guide.md), but here's the short version:

1. Create `connectors/your_exchange.py`
2. Implement the methods defined in `core/interface.py`
3. Register it in `connectors/__init__.py`
4. Write tests in `tests/test_your_exchange.py`
5. Submit a pull request

The Bybit connector (`connectors/bybit.py`) is the reference implementation — use it as your template.

## Project Roadmap

We're building this in the open, and we'd love your input on what matters most.

| Phase | Status | Description |
| :--- | :--- | :--- |
| UTI v0.1 | Done | Core specification, data models, Bybit connector |
| MCP Server | Done | REST API with tool discovery, risk management |
| WebSocket Support | Planned | Real-time market data streaming |
| Additional Connectors | Planned | Binance, Coinbase, Kraken, Interactive Brokers |
| Enterprise Add-ons | Planned | Proprietary connectors (SAP, Bloomberg), advanced algos |
| Hosted Gateway | Planned | Managed cloud service with credential vault and audit logs |
| UTI v1.0 | Planned | Stable specification after community feedback |

## Contributing

We welcome contributions of all kinds — bug fixes, new connectors, documentation improvements, or just feedback on the design. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

The most impactful contributions right now:

- **New exchange connectors** — every connector makes the standard more useful
- **Bug reports and edge cases** — help us harden the UTI
- **Documentation** — tutorials, guides, translations
- **Feedback on the UTI design** — we want this to be a community standard

## Enterprise and Institutional Use

The open-source core is designed to be production-ready for individual developers and small teams. For organisations with advanced requirements — regulatory compliance, legacy system integration, advanced execution algorithms, or managed infrastructure — we offer enterprise solutions.

See [enterprise/README.md](enterprise/README.md) and [gateway/README.md](gateway/README.md) for details, or reach out at **enterprise@mcpfoundry.dev**.

## License

This project is licensed under the [Apache License 2.0](LICENSE) — use it freely in personal and commercial projects.

## Acknowledgements

This project exists because we believe the future of trading is agentic, and that future needs an open standard. We're grateful to everyone who contributes to making that happen.

---

**Built with care by the MCP Foundry community.**
