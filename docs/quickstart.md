# Quick Start Guide

This guide gets you from zero to a running MCP Foundry server in under five minutes.

## Prerequisites

- Python 3.11 or later
- A Bybit account (testnet is fine — [register here](https://testnet.bybit.com/))
- Your Bybit API key and secret

## Installation

### Option A: From source (recommended for development)

```bash
git clone https://github.com/mcp-foundry/mcp-foundry.git
cd mcp-foundry
pip install -e ".[dev]"
```

### Option B: Docker

```bash
docker pull ghcr.io/mcp-foundry/mcp-foundry:latest
```

## Configuration

### 1. Set your credentials

Copy the example environment file and fill in your API credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
EXCHANGE_API_KEY=your_api_key_here
EXCHANGE_API_SECRET=your_api_secret_here
EXCHANGE_TESTNET=true
MCP_EXCHANGE=bybit
```

### 2. (Optional) Customise risk settings

Edit `config/config.yaml` to adjust risk parameters:

```yaml
risk:
  max_risk_per_trade_pct: 2.0
  max_position_size_pct: 10.0
  max_open_positions: 5
```

## Start the Server

```bash
python scripts/run_server.py
```

You should see:

```
  MCP Foundry — Trading Server
  Listening on http://0.0.0.0:8000
  API docs at  http://0.0.0.0:8000/docs
```

## Verify It Works

### Check the health endpoint

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "exchange": "bybit",
  "testnet": true,
  "connected": true
}
```

### Get a price quote

```bash
curl http://localhost:8000/market/ticker/BTCUSDT
```

### Discover available tools

```bash
curl http://localhost:8000/tools | python -m json.tool
```

This returns the list of trading tools that any AI agent can use.

## Connect an AI Agent

The MCP server exposes a standard REST API. Any agent that can make HTTP requests can trade through it. Here's a minimal Python example:

```python
import requests

SERVER = "http://localhost:8000"

# Get available tools
tools = requests.get(f"{SERVER}/tools").json()
print(f"Available tools: {[t['name'] for t in tools]}")

# Get BTC price
ticker = requests.get(f"{SERVER}/market/ticker/BTCUSDT").json()
print(f"BTC price: {ticker['last_price']}")

# Place a small market buy (uncomment to execute)
# order = requests.post(f"{SERVER}/trade/place_order", json={
#     "symbol": "BTCUSDT",
#     "side": "buy",
#     "qty": 0.001,
# }).json()
# print(f"Order: {order}")
```

## Next Steps

- **Run the examples** — See the `examples/` directory for more integration patterns.
- **Read the architecture guide** — [docs/architecture.md](architecture.md) explains how everything fits together.
- **Build a connector** — [docs/connector_development_guide.md](connector_development_guide.md) shows how to add new exchanges.
- **Join the community** — Open a [GitHub Discussion](https://github.com/mcp-foundry/mcp-foundry/discussions) to share your use case.

## Using Docker

If you prefer Docker:

```bash
docker run -p 8000:8000 \
  -e EXCHANGE_API_KEY=your_key \
  -e EXCHANGE_API_SECRET=your_secret \
  -e EXCHANGE_TESTNET=true \
  ghcr.io/mcp-foundry/mcp-foundry:latest
```

Or with Docker Compose:

```bash
docker-compose up
```

## Troubleshooting

**"Connection refused" when calling the server**
Make sure the server is running and listening on the expected port. Check the terminal output for errors.

**"Authentication failed" from the exchange**
Double-check your API key and secret in `.env`. If using Bybit testnet, make sure you created the keys on `testnet.bybit.com`, not the mainnet.

**"Rate limit exceeded"**
The connector has built-in retry logic with exponential back-off. If you're still hitting limits, reduce the frequency of your requests.

If you're stuck, open a [GitHub Issue](https://github.com/mcp-foundry/mcp-foundry/issues) with the error message and we'll help you out.
