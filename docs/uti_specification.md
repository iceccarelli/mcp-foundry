# Universal Trading Interface (UTI) Specification

**Version:** 0.1.0
**Status:** Draft — open for community feedback

## Purpose

The Universal Trading Interface (UTI) defines a standard contract for connecting software agents to financial markets. It specifies the data models, method signatures, and error handling conventions that every compliant connector must implement.

The goal is to solve the **M x N integration problem**: if you have M agents and N exchanges, you currently need M x N custom integrations. With the UTI, you need M + N — each agent implements the UTI client once, each exchange gets one connector, and they all interoperate.

## Scope

The UTI covers:

- **Order management** — placing, cancelling, and querying orders
- **Account data** — wallet balance and open positions
- **Market data** — tickers, order books, and historical candles
- **Connectivity** — health checks and exchange metadata

The UTI does not cover:

- Specific trading strategies or algorithms
- User interface or visualisation
- Regulatory compliance (this is handled by the enterprise layer)

## Data Models

All data models are immutable (frozen dataclasses). This ensures that data flowing through the system cannot be accidentally modified.

### OrderSpec

Describes an order to be placed.

| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `symbol` | `str` | Yes | — | Trading pair (e.g., `"BTCUSDT"`) |
| `side` | `str` | Yes | — | `"buy"` or `"sell"` |
| `qty` | `float` | Yes | — | Quantity in base asset units |
| `order_type` | `str` | No | `"market"` | `"market"` or `"limit"` |
| `price` | `float` | No | `None` | Limit price (required for limit orders) |
| `time_in_force` | `str` | No | `None` | `"gtc"`, `"ioc"`, `"fok"`, or `"post_only"` |
| `take_profit` | `float` | No | `None` | Take-profit trigger price |
| `stop_loss` | `float` | No | `None` | Stop-loss trigger price |
| `reduce_only` | `bool` | No | `False` | If `True`, only reduces an existing position |
| `leverage` | `int` | No | `None` | Position leverage |
| `params` | `dict` | No | `None` | Exchange-specific parameters |

### OrderResponse

Describes the result of an order operation.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `order_id` | `str` | — | Exchange-assigned order identifier |
| `symbol` | `str` | — | Trading pair |
| `side` | `str` | — | `"buy"` or `"sell"` |
| `order_type` | `str` | — | `"market"` or `"limit"` |
| `qty` | `float` | — | Requested quantity |
| `filled_qty` | `float` | `0.0` | Quantity filled so far |
| `price` | `float` | `None` | Limit price (if applicable) |
| `avg_fill_price` | `float` | `None` | Average fill price |
| `status` | `str` | `"new"` | Order status |
| `timestamp` | `int` | `None` | Creation timestamp (milliseconds) |
| `raw` | `dict` | `None` | Raw exchange response |

### TickerData

Latest market summary for a trading pair.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `symbol` | `str` | — | Trading pair |
| `last_price` | `float` | — | Last traded price |
| `bid` | `float` | `None` | Best bid price |
| `ask` | `float` | `None` | Best ask price |
| `high_24h` | `float` | `None` | 24-hour high |
| `low_24h` | `float` | `None` | 24-hour low |
| `volume_24h` | `float` | `None` | 24-hour volume |
| `timestamp` | `int` | `None` | Timestamp (milliseconds) |

### OrderBookData

Current order book snapshot.

| Field | Type | Description |
| :--- | :--- | :--- |
| `symbol` | `str` | Trading pair |
| `bids` | `List[OrderBookEntry]` | Bid levels (price, quantity) |
| `asks` | `List[OrderBookEntry]` | Ask levels (price, quantity) |
| `timestamp` | `int` | Snapshot timestamp (milliseconds) |

### CandleData

A single OHLCV candlestick.

| Field | Type | Description |
| :--- | :--- | :--- |
| `timestamp` | `int` | Candle open time (milliseconds) |
| `open` | `float` | Open price |
| `high` | `float` | High price |
| `low` | `float` | Low price |
| `close` | `float` | Close price |
| `volume` | `float` | Volume |

### BalanceData

Account balance summary.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `total_equity` | `float` | — | Total account equity |
| `available_balance` | `float` | — | Balance available for trading |
| `currency` | `str` | `"USDT"` | Settlement currency |
| `assets` | `list` | `[]` | Per-asset breakdown |

### PositionData

An open position.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `symbol` | `str` | — | Trading pair |
| `side` | `str` | — | `"long"` or `"short"` |
| `size` | `float` | — | Position size in base asset |
| `entry_price` | `float` | — | Average entry price |
| `mark_price` | `float` | `None` | Current mark price |
| `unrealised_pnl` | `float` | `None` | Unrealised profit/loss |
| `leverage` | `int` | `None` | Position leverage |
| `liquidation_price` | `float` | `None` | Estimated liquidation price |

## Enumerations

| Enum | Values |
| :--- | :--- |
| `OrderSide` | `buy`, `sell` |
| `OrderType` | `market`, `limit`, `stop_market`, `stop_limit`, `trailing_stop` |
| `TimeInForce` | `gtc`, `ioc`, `fok`, `post_only` |
| `OrderStatus` | `new`, `partially_filled`, `filled`, `cancelled`, `rejected`, `expired` |

## Required Methods

Every UTI-compliant connector must implement the following methods:

### Order Management

| Method | Signature | Description |
| :--- | :--- | :--- |
| `place_order` | `(spec: OrderSpec) -> OrderResponse` | Place a new order |
| `cancel_order` | `(symbol: str, order_id: str) -> OrderResponse` | Cancel an order |
| `get_order` | `(symbol: str, order_id: str) -> OrderResponse` | Get order details |
| `get_open_orders` | `(symbol: str = None) -> List[OrderResponse]` | List open orders |

### Account Data

| Method | Signature | Description |
| :--- | :--- | :--- |
| `get_wallet_balance` | `() -> BalanceData` | Get account balance |
| `get_positions` | `(symbol: str = None) -> List[PositionData]` | Get open positions |

### Market Data

| Method | Signature | Description |
| :--- | :--- | :--- |
| `get_ticker` | `(symbol: str) -> TickerData` | Get latest ticker |
| `get_orderbook` | `(symbol: str, depth: int = 25) -> OrderBookData` | Get order book |
| `get_candles` | `(symbol: str, interval: str, limit: int) -> List[CandleData]` | Get historical candles |

### Connectivity

| Method | Signature | Description |
| :--- | :--- | :--- |
| `ping` | `() -> bool` | Health check |
| `get_exchange_info` | `() -> Dict[str, Any]` | Exchange metadata |

## Error Handling

All errors must be raised as subclasses of `UTIError`. Each exception carries:

- `message` — Human-readable description
- `code` — Exchange-specific error code (optional)
- `raw` — Raw exchange response for debugging (optional)

See `core/exceptions.py` for the full hierarchy.

## Versioning

The UTI follows semantic versioning:

- **Patch** (0.1.x) — Bug fixes, clarifications
- **Minor** (0.x.0) — New optional fields or methods (backward-compatible)
- **Major** (x.0.0) — Breaking changes to existing fields or methods

## Feedback

This specification is a living document. If you have suggestions, questions, or concerns, please open a [GitHub Discussion](https://github.com/mcp-foundry/mcp-foundry/discussions). We want this to be a community standard, and that means your input matters.
