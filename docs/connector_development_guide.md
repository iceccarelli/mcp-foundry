# Connector Development Guide

This guide walks you through building a new exchange connector for the MCP Foundry. By the end, you'll have a fully functional connector that any AI agent can use through the MCP server.

## Before You Start

Read through the [UTI Specification](uti_specification.md) to understand the data models and method signatures your connector needs to implement. Then look at `connectors/bybit.py` — it's the reference implementation and the best template to work from.

## Step 1: Create Your Connector File

Create a new file at `connectors/your_exchange.py`. Start with the imports and class skeleton:

```python
"""
YourExchange Connector
=======================

UTI connector for the YourExchange API.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp

from core.exceptions import (
    AuthenticationError,
    ConnectionError,
    ExchangeError,
    InsufficientFundsError,
    InvalidOrderError,
    OrderNotFoundError,
    RateLimitError,
)
from core.interface import (
    BalanceData,
    CandleData,
    OrderBookData,
    OrderBookEntry,
    OrderResponse,
    OrderSpec,
    PositionData,
    TickerData,
)

logger = logging.getLogger(__name__)


class YourExchangeConnector:
    """UTI connector for YourExchange."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        category: str = "linear",
        timeout: int = 10,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.category = category
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
```

## Step 2: Implement the Required Methods

Your connector must implement every method listed in the UTI specification. Here's a checklist:

### Order Management

- [ ] `place_order(spec: OrderSpec) -> OrderResponse`
- [ ] `cancel_order(symbol: str, order_id: str) -> OrderResponse`
- [ ] `get_order(symbol: str, order_id: str) -> OrderResponse`
- [ ] `get_open_orders(symbol: Optional[str] = None) -> List[OrderResponse]`

### Account Data

- [ ] `get_wallet_balance() -> BalanceData`
- [ ] `get_positions(symbol: Optional[str] = None) -> List[PositionData]`

### Market Data

- [ ] `get_ticker(symbol: str) -> TickerData`
- [ ] `get_orderbook(symbol: str, depth: int = 25) -> OrderBookData`
- [ ] `get_candles(symbol: str, interval: str, limit: int) -> List[CandleData]`

### Connectivity

- [ ] `ping() -> bool`
- [ ] `get_exchange_info() -> Dict[str, Any]`

### Lifecycle

- [ ] `close() -> None`

## Step 3: Handle Authentication

Most exchanges use HMAC-SHA256 signing. Create a private `_sign()` method and an `_auth_headers()` method. See the Bybit connector for a complete example.

Key points:

- Use the exchange's documented signing algorithm exactly.
- Include a timestamp in every signed request.
- Set an appropriate receive window to prevent replay attacks.

## Step 4: Implement Retry Logic

Network requests fail. Your connector should retry transient failures with exponential back-off:

```python
async def _request(self, method: str, path: str, ...) -> Dict[str, Any]:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Make the request
            ...
        except aiohttp.ClientError as exc:
            if attempt == MAX_RETRIES:
                raise ConnectionError(
                    message=f"Failed after {MAX_RETRIES} attempts: {exc}"
                ) from exc
            await asyncio.sleep(BACKOFF * (2 ** (attempt - 1)))
```

## Step 5: Translate Errors

Map the exchange's error codes to UTI exceptions. This is critical — it's what makes the error handling consistent across all connectors.

```python
@staticmethod
def _raise_for_code(code: int, msg: str, raw: dict) -> None:
    if code in (AUTH_ERROR_CODES):
        raise AuthenticationError(message=msg, code=str(code), raw=raw)
    if code in (INSUFFICIENT_FUNDS_CODES):
        raise InsufficientFundsError(message=msg, code=str(code), raw=raw)
    # ... and so on
    raise ExchangeError(message=msg, code=str(code), raw=raw)
```

## Step 6: Register Your Connector

Open `connectors/__init__.py` and add your connector:

```python
from connectors.your_exchange import YourExchangeConnector

register_connector("your_exchange", YourExchangeConnector)
```

That's it. The MCP server will now be able to load your connector by setting `MCP_EXCHANGE=your_exchange`.

## Step 7: Write Tests

Create `tests/test_your_exchange.py`. Use the mock patterns from `tests/conftest.py` — never hit a real exchange in tests.

At minimum, test:

- Connector initialisation (testnet vs. mainnet URL, category)
- Error translation (each error code maps to the right exception)
- Data normalisation (exchange response → UTI data model)
- Authentication (signature generation)

## Step 8: Submit a Pull Request

Once your tests pass:

1. Update the README to list your connector.
2. Add a brief entry to the changelog.
3. Open a pull request with a clear description of what the connector supports.

We'll review it carefully and work with you to get it merged.

## Tips

- **Start with market data** — `get_ticker()` and `get_candles()` are the easiest to implement and test.
- **Use the Bybit connector as your template** — copy its structure and adapt it.
- **Log generously** — use `logger.info()` for key operations and `logger.warning()` for recoverable errors.
- **Don't swallow exceptions** — if something fails, raise the appropriate UTI exception with context.
- **Test on testnet first** — most exchanges offer a testnet. Use it.

## Questions?

If you get stuck, open a [GitHub Discussion](https://github.com/mcp-foundry/mcp-foundry/discussions). We're happy to help.
