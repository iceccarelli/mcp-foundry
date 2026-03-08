# Architecture Guide

This document describes the internal architecture of the MCP Foundry, how the components fit together, and the design decisions behind them.

## Overview

The MCP Foundry is organised as a layered system. Each layer has a single responsibility and communicates with adjacent layers through well-defined interfaces. This makes it possible to swap any layer without affecting the others.

```
┌──────────────────────────────────────────────────────────────┐
│                        AI Agents                              │
│            Claude, GPT, LangChain, custom agents              │
├──────────────────────────────────────────────────────────────┤
│                     MCP Server Layer                          │
│       FastAPI REST API — tool discovery, authentication       │
│                   core/mcp_server.py                          │
├──────────────────────────────────────────────────────────────┤
│                   Application Layer                           │
│     Trading Engine (core/trading_engine.py)                   │
│     Risk Manager  (core/risk_management.py)                   │
├──────────────────────────────────────────────────────────────┤
│              Universal Trading Interface                      │
│         The contract — core/interface.py                      │
│     Data models, enumerations, protocol definition            │
├──────────────────────────────────────────────────────────────┤
│                  Connector Layer                              │
│        Bybit (connectors/bybit.py)                            │
│        Future: Binance, Coinbase, Kraken, IBKR                │
└──────────────────────────────────────────────────────────────┘
```

## Layer Details

### 1. Universal Trading Interface (`core/interface.py`)

This is the heart of the project. It defines:

**Data Models** — Frozen dataclasses that represent every piece of trading data:

| Model | Purpose |
| :--- | :--- |
| `OrderSpec` | Describes an order to be placed |
| `OrderResponse` | Describes the result of an order operation |
| `TickerData` | Latest price and market summary |
| `OrderBookData` | Current bids and asks |
| `CandleData` | OHLCV candlestick data |
| `BalanceData` | Account balance and equity |
| `PositionData` | Open position details |

**Enumerations** — Standardised values for order sides, types, time-in-force, and statuses.

**Protocol** — A Python `Protocol` class (`UniversalTradingInterface`) that defines the contract every connector must implement. This uses structural subtyping, so connectors don't need to inherit from a base class — they just need to implement the right methods with the right signatures.

### 2. Connector Layer (`connectors/`)

Each connector translates UTI calls into exchange-specific API calls and translates the responses back into UTI data models. The connector is responsible for:

- Authentication (signing requests)
- Rate limiting and retry logic
- Error translation (exchange error codes to UTI exceptions)
- Data normalisation (exchange-specific formats to UTI models)

The Bybit connector (`connectors/bybit.py`) is the reference implementation. It demonstrates all of these responsibilities.

**Connector Registry** — The `connectors/__init__.py` module maintains a registry that maps exchange names to connector classes. This allows the MCP server to load connectors dynamically based on configuration.

### 3. Application Layer

**Trading Engine** (`core/trading_engine.py`) — Provides higher-level convenience methods built on top of the UTI. It holds a reference to any UTI-compatible connector and exposes methods like `execute_market_buy()`, `close_position()`, and `get_account_summary()`. The engine is exchange-agnostic by design.

**Risk Manager** (`core/risk_management.py`) — Sits between the strategy and the exchange. It validates proposed trades against configurable rules:

- Per-trade risk limits (percentage of equity)
- Single-position exposure caps
- Total portfolio exposure limits
- Maximum number of open positions
- Daily loss limits
- Minimum balance reserves

All checks use live account data fetched through the UTI.

### 4. MCP Server Layer (`core/mcp_server.py`)

A FastAPI application that exposes the UTI as a REST API. Key design decisions:

**Tool Discovery** — The `/tools` endpoint returns a list of available trading tools in a format that AI agents can parse and use. This follows the Model Context Protocol pattern where agents discover capabilities at runtime.

**Automatic Validation** — Pydantic models validate all incoming requests. Invalid parameters are rejected with clear error messages before they reach the exchange.

**Risk Integration** — Every order passes through the Risk Manager before execution. This is not optional — it's built into the server's order flow.

**Error Translation** — UTI exceptions are mapped to appropriate HTTP status codes:

| UTI Exception | HTTP Status |
| :--- | :--- |
| `AuthenticationError` | 401 |
| `InvalidOrderError` | 400 |
| `OrderNotFoundError` | 404 |
| `InsufficientFundsError` | 422 |
| `RateLimitError` | 429 |
| Other `UTIError` | 500 |

## Exception Hierarchy

All exceptions inherit from `UTIError`, which carries a human-readable message, an optional exchange error code, and the raw response for debugging:

```
UTIError
├── ConnectionError      — Network or connectivity issues
├── AuthenticationError   — Invalid or expired credentials
├── ExchangeError         — General exchange-side errors
│   ├── InvalidOrderError     — Rejected order parameters
│   ├── InsufficientFundsError — Not enough balance
│   └── OrderNotFoundError     — Order doesn't exist
└── RateLimitError        — Too many requests
```

## Data Flow: Placing an Order

Here's what happens when an AI agent places an order through the MCP server:

```
Agent HTTP POST /trade/place_order
        │
        ▼
   MCP Server (Pydantic validation)
        │
        ▼
   Risk Manager (validate_trade)
        │  ✓ passes all checks
        ▼
   Trading Engine / Connector
        │
        ▼
   OrderSpec → Bybit API call
        │
        ▼
   Bybit response → OrderResponse
        │
        ▼
   JSON response to agent
```

If any step fails, the appropriate exception is raised and translated into an HTTP error response with a clear message.

## Configuration

Configuration follows an environment-first approach:

1. **Environment variables** — Always take precedence. Ideal for Docker and CI/CD.
2. **YAML config file** — For local development and complex setups.
3. **Built-in defaults** — Sensible defaults for everything.

See `utils/config_loader.py` for the implementation and `config/config.yaml` for the reference configuration file.

## Testing Strategy

The test suite uses mocked connectors exclusively — no tests hit real exchanges. The `tests/conftest.py` module provides:

- `mock_connector` — A fully mocked UTI connector with realistic return values
- `sample_ticker`, `sample_balance`, `sample_position` — Realistic test data
- `sample_order_response` — A realistic order response

This makes tests fast, deterministic, and safe to run in CI.

## Design Principles

1. **Interface over implementation** — The UTI protocol is the contract. Everything else is an implementation detail.
2. **Exchange-agnostic by default** — The trading engine and risk manager never import exchange-specific code.
3. **Fail loudly** — Exceptions carry context. Silent failures are bugs.
4. **Configuration over convention** — Risk parameters, exchange selection, and server settings are all configurable.
5. **Test without side effects** — The mock connector makes it possible to test everything without network calls.
