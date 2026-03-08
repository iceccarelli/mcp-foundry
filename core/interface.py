# MCP Foundry for Trading — Universal Trading Interface (UTI) Specification
# Created for the MCP Foundry project
# Version: 0.1.0
#
# This file defines the Universal Trading Interface (UTI) — an open standard
# for connecting AI agents to financial markets. Every connector, whether
# open-source or enterprise, implements this protocol.

"""
Universal Trading Interface (UTI) — Protocol Specification
===========================================================

The UTI is a Python ``Protocol`` that defines the contract between AI agents
and financial exchanges. It is intentionally exchange-agnostic, asset-class-
agnostic, and framework-agnostic.

**Design Principles:**

1. **Universality** — Any exchange, broker, or financial system can implement
   the UTI regardless of its underlying API.
2. **Determinism** — Every method returns strongly-typed dataclasses so that
   agents can reason about results without parsing opaque dictionaries.
3. **Safety** — All operations raise well-defined exceptions from
   ``core.exceptions`` so that agents can handle errors gracefully.
4. **Extensibility** — The ``params`` field on ``OrderSpec`` allows
   exchange-specific options without breaking the standard interface.

We think of the UTI as **USB-C for trading** — one plug that works everywhere.
This is just the beginning, and we'd love your help making it better.

**Versioning:**

The UTI follows `Semantic Versioning <https://semver.org/>`_. Breaking changes
to the protocol increment the major version. New optional methods increment
the minor version.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class OrderSide(enum.StrEnum):
    """Side of a trading order."""
    BUY = "buy"
    SELL = "sell"


class OrderType(enum.StrEnum):
    """Type of a trading order."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"
    TAKE_PROFIT_MARKET = "take_profit_market"
    TAKE_PROFIT_LIMIT = "take_profit_limit"


class TimeInForce(enum.StrEnum):
    """Time-in-force policy for limit orders."""
    GTC = "gtc"   # Good Till Cancel
    IOC = "ioc"   # Immediate Or Cancel
    FOK = "fok"   # Fill Or Kill
    POST_ONLY = "post_only"


class OrderStatus(enum.StrEnum):
    """Lifecycle status of an order."""
    NEW = "new"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PositionSide(enum.StrEnum):
    """Side of an open position."""
    LONG = "long"
    SHORT = "short"
    NONE = "none"


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OrderSpec:
    """
    Specification for placing a new order.

    This is the universal input model accepted by every UTI connector.

    Attributes:
        symbol: Trading pair symbol (e.g., ``"BTCUSDT"``).
        side: Order side — ``"buy"`` or ``"sell"``.
        qty: Order quantity in base asset units.
        order_type: Order type (default ``"market"``).
        price: Limit price. Required for limit orders; ignored for market.
        time_in_force: Time-in-force policy (default ``None`` — exchange default).
        take_profit: Optional take-profit trigger price.
        stop_loss: Optional stop-loss trigger price.
        reduce_only: If ``True``, the order can only reduce an existing position.
        leverage: Desired leverage for the position (futures only).
        params: Arbitrary exchange-specific parameters. Connectors MAY use
                these but MUST NOT require them for standard operations.
    """
    symbol: str
    side: str
    qty: float
    order_type: str = "market"
    price: float | None = None
    time_in_force: str | None = None
    take_profit: float | None = None
    stop_loss: float | None = None
    reduce_only: bool = False
    leverage: int | None = None
    params: dict[str, Any] | None = field(default_factory=dict)


@dataclass(frozen=True)
class OrderResponse:
    """
    Standardized response returned after placing, cancelling, or querying an order.

    Attributes:
        order_id: Exchange-assigned order identifier.
        symbol: Trading pair symbol.
        side: Order side.
        order_type: Order type.
        qty: Requested quantity.
        filled_qty: Quantity filled so far.
        price: Limit price (``None`` for market orders).
        avg_fill_price: Average fill price (``None`` if not yet filled).
        status: Current order status.
        timestamp: Unix timestamp in milliseconds when the order was created.
        raw: The raw exchange response for debugging and advanced use.
    """
    order_id: str
    symbol: str
    side: str
    order_type: str
    qty: float
    filled_qty: float = 0.0
    price: float | None = None
    avg_fill_price: float | None = None
    status: str = "new"
    timestamp: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TickerData:
    """
    Latest ticker snapshot for a trading pair.

    Attributes:
        symbol: Trading pair symbol.
        last_price: Last traded price.
        bid: Best bid price.
        ask: Best ask price.
        high_24h: 24-hour high.
        low_24h: 24-hour low.
        volume_24h: 24-hour trading volume in base asset.
        timestamp: Unix timestamp in milliseconds.
    """
    symbol: str
    last_price: float
    bid: float | None = None
    ask: float | None = None
    high_24h: float | None = None
    low_24h: float | None = None
    volume_24h: float | None = None
    timestamp: int | None = None


@dataclass(frozen=True)
class BalanceData:
    """
    Wallet balance snapshot.

    Attributes:
        total_equity: Total account equity in the settlement currency.
        available_balance: Balance available for new orders.
        currency: Settlement currency (e.g., ``"USDT"``).
        assets: Per-asset breakdown as a list of dictionaries.
    """
    total_equity: float
    available_balance: float
    currency: str = "USDT"
    assets: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class PositionData:
    """
    Open position snapshot.

    Attributes:
        symbol: Trading pair symbol.
        side: Position side (``"long"`` or ``"short"``).
        size: Position size in base asset units.
        entry_price: Average entry price.
        mark_price: Current mark price.
        unrealised_pnl: Unrealised profit/loss.
        leverage: Current leverage.
        liquidation_price: Estimated liquidation price.
    """
    symbol: str
    side: str
    size: float
    entry_price: float
    mark_price: float | None = None
    unrealised_pnl: float | None = None
    leverage: int | None = None
    liquidation_price: float | None = None


@dataclass(frozen=True)
class CandleData:
    """
    Single OHLCV candlestick.

    Attributes:
        timestamp: Candle open time as Unix milliseconds.
        open: Open price.
        high: High price.
        low: Low price.
        close: Close price.
        volume: Volume in base asset.
    """
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class OrderBookEntry:
    """Single price level in the order book."""
    price: float
    qty: float


@dataclass(frozen=True)
class OrderBookData:
    """
    Order book snapshot.

    Attributes:
        symbol: Trading pair symbol.
        bids: List of bid entries sorted by price descending.
        asks: List of ask entries sorted by price ascending.
        timestamp: Unix timestamp in milliseconds.
    """
    symbol: str
    bids: list[OrderBookEntry] = field(default_factory=list)
    asks: list[OrderBookEntry] = field(default_factory=list)
    timestamp: int | None = None


# ---------------------------------------------------------------------------
# The Universal Trading Interface (UTI) Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class UniversalTradingInterface(Protocol):
    """
    The Universal Trading Interface (UTI) — Version 0.1.0
    ======================================================

    This is the protocol that every connector in the MCP Foundry ecosystem
    implements. It defines the complete surface area through which AI agents
    interact with financial markets.

    **Contract guarantees:**

    - All methods are ``async`` to support high-throughput, non-blocking I/O.
    - All methods return strongly-typed dataclasses defined above.
    - All methods raise exceptions from ``core.exceptions`` on failure.
    - Implementations should be thread-safe for concurrent agent access.

    **How to build a new connector:**

    1. Create a new file under ``connectors/`` (e.g., ``connectors/binance.py``).
    2. Define a class that implements every method in this protocol.
    3. Register the connector in ``connectors/__init__.py``.
    4. Write tests under ``tests/`` using the provided mock fixtures.

    See ``connectors/bybit.py`` for the reference implementation.
    We welcome community-contributed connectors — the more exchanges we
    support, the more useful this standard becomes for everyone.
    """

    # ---- Order Management ---------------------------------------------------

    async def place_order(self, spec: OrderSpec) -> OrderResponse:
        """
        Place a new order on the exchange.

        Args:
            spec: An ``OrderSpec`` describing the desired order.

        Returns:
            An ``OrderResponse`` with the exchange-assigned order ID and
            initial status.

        Raises:
            InvalidOrderError: If the order parameters are invalid.
            InsufficientFundsError: If the account lacks sufficient margin.
            RateLimitError: If the exchange rate limit has been exceeded.
            ExchangeError: For any other exchange-side failure.
        """
        ...

    async def cancel_order(self, symbol: str, order_id: str) -> OrderResponse:
        """
        Cancel an existing open order.

        Args:
            symbol: Trading pair symbol.
            order_id: The exchange-assigned order identifier.

        Returns:
            An ``OrderResponse`` reflecting the cancelled state.

        Raises:
            OrderNotFoundError: If the order does not exist or is already filled.
            ExchangeError: For any other exchange-side failure.
        """
        ...

    async def get_order(self, symbol: str, order_id: str) -> OrderResponse:
        """
        Retrieve the current state of a specific order.

        Args:
            symbol: Trading pair symbol.
            order_id: The exchange-assigned order identifier.

        Returns:
            An ``OrderResponse`` with the latest status and fill information.

        Raises:
            OrderNotFoundError: If the order does not exist.
        """
        ...

    async def get_open_orders(
        self, symbol: str | None = None
    ) -> list[OrderResponse]:
        """
        Retrieve all open (unfilled) orders.

        Args:
            symbol: If provided, filter orders to this symbol only.

        Returns:
            A list of ``OrderResponse`` objects for each open order.
        """
        ...

    # ---- Account & Position -------------------------------------------------

    async def get_wallet_balance(self) -> BalanceData:
        """
        Retrieve the current wallet balance and equity.

        Returns:
            A ``BalanceData`` snapshot of the account.

        Raises:
            AuthenticationError: If API credentials are invalid.
            ConnectionError: If the exchange is unreachable.
        """
        ...

    async def get_positions(
        self, symbol: str | None = None
    ) -> list[PositionData]:
        """
        Retrieve open positions.

        Args:
            symbol: If provided, filter to this symbol only.

        Returns:
            A list of ``PositionData`` objects for each open position.
        """
        ...

    # ---- Market Data --------------------------------------------------------

    async def get_ticker(self, symbol: str) -> TickerData:
        """
        Retrieve the latest ticker for a trading pair.

        Args:
            symbol: Trading pair symbol (e.g., ``"BTCUSDT"``).

        Returns:
            A ``TickerData`` snapshot.
        """
        ...

    async def get_orderbook(
        self, symbol: str, depth: int = 25
    ) -> OrderBookData:
        """
        Retrieve the current order book.

        Args:
            symbol: Trading pair symbol.
            depth: Number of price levels per side (default 25).

        Returns:
            An ``OrderBookData`` snapshot.
        """
        ...

    async def get_candles(
        self,
        symbol: str,
        interval: str = "1m",
        limit: int = 200,
    ) -> list[CandleData]:
        """
        Retrieve historical OHLCV candlestick data.

        Args:
            symbol: Trading pair symbol.
            interval: Candle interval (e.g., ``"1m"``, ``"5m"``, ``"1h"``, ``"1d"``).
            limit: Maximum number of candles to return (default 200).

        Returns:
            A list of ``CandleData`` objects ordered by timestamp ascending.
        """
        ...

    # ---- Connectivity -------------------------------------------------------

    async def ping(self) -> bool:
        """
        Health-check the connection to the exchange API.

        Returns:
            ``True`` if the exchange is reachable and authenticated.
        """
        ...

    async def get_exchange_info(self) -> dict[str, Any]:
        """
        Retrieve exchange metadata (supported symbols, tick sizes, lot sizes).

        Returns:
            A dictionary of exchange-specific metadata.
        """
        ...
