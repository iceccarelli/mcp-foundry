# MCP Foundry for Trading — Bybit V5 Connector
# Created for the MCP Foundry project
#
# This is the reference implementation of the Universal Trading Interface (UTI)
# for the Bybit V5 API. It demonstrates how to build a production-quality
# connector that any AI agent can use through the MCP server.

"""
Bybit V5 Connector
====================

The first open-source UTI connector. It wraps the Bybit V5 unified API and
translates every call into the standardized UTI data models.

**Supported features:**

- Spot and linear perpetual futures trading
- Full order lifecycle (place, cancel, query)
- Wallet balance and position queries
- Market data (ticker, order book, candles)
- Automatic rate-limit awareness with exponential back-off
- Comprehensive logging for observability

**Quick start:**

.. code-block:: python

    from connectors.bybit import BybitConnector

    connector = BybitConnector(
        api_key="YOUR_KEY",
        api_secret="YOUR_SECRET",
        testnet=True,  # always start on testnet
    )
    ticker = await connector.get_ticker("BTCUSDT")
    print(ticker.last_price)

If you find a bug or want to improve this connector, we'd love a pull request.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import time
from typing import Any
from urllib.parse import urlencode

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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAINNET_BASE = "https://api.bybit.com"
_TESTNET_BASE = "https://api-testnet.bybit.com"
_RECV_WINDOW = "5000"
_MAX_RETRIES = 3
_RETRY_BACKOFF = 0.5  # seconds, doubles each retry


# ---------------------------------------------------------------------------
# Bybit Connector
# ---------------------------------------------------------------------------


class BybitConnector:
    """
    Production-ready UTI connector for the Bybit V5 unified API.

    This class implements every method defined in
    :class:`core.interface.UniversalTradingInterface`.

    Args:
        api_key: Your Bybit API key.
        api_secret: Your Bybit API secret.
        testnet: If ``True``, connect to the Bybit testnet (recommended for
                 development and testing).
        category: Account category — ``"linear"`` for USDT perpetuals,
                  ``"spot"`` for spot trading.
        timeout: HTTP request timeout in seconds (default 10).
    """

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
        self._base_url = _TESTNET_BASE if testnet else _MAINNET_BASE
        self._session: aiohttp.ClientSession | None = None
        logger.info(
            "BybitConnector initialised — testnet=%s, category=%s",
            testnet,
            category,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_session(self) -> aiohttp.ClientSession:
        """Lazily create and return an ``aiohttp`` session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    def _sign(self, timestamp: str, params_str: str) -> str:
        """Generate HMAC-SHA256 signature for Bybit V5 authentication."""
        sign_payload = f"{timestamp}{self.api_key}{_RECV_WINDOW}{params_str}"
        return hmac.new(
            self.api_secret.encode("utf-8"),
            sign_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _auth_headers(self, params_str: str = "") -> dict[str, str]:
        """Build authenticated request headers."""
        ts = str(int(time.time() * 1000))
        return {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": self._sign(ts, params_str),
            "X-BAPI-SIGN-TYPE": "2",
            "X-BAPI-TIMESTAMP": ts,
            "X-BAPI-RECV-WINDOW": _RECV_WINDOW,
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        signed: bool = False,
    ) -> dict[str, Any]:
        """
        Execute an HTTP request against the Bybit V5 API with retry logic.

        Raises appropriate UTI exceptions based on the Bybit error codes.
        """
        import json as _json

        session = await self._get_session()
        url = f"{self._base_url}{path}"

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                if signed:
                    if method == "GET" and params:
                        params_str = urlencode(sorted(params.items()))
                        headers = self._auth_headers(params_str)
                    elif body:
                        params_str = _json.dumps(body)
                        headers = self._auth_headers(params_str)
                    else:
                        headers = self._auth_headers("")
                else:
                    headers = {"Content-Type": "application/json"}

                if method == "GET":
                    resp = await session.get(url, params=params, headers=headers)
                else:
                    resp = await session.post(url, json=body, headers=headers)

                data = await resp.json()

                # Bybit returns retCode 0 on success
                ret_code = data.get("retCode", -1)
                if ret_code == 0:
                    return data.get("result", {})

                # Map Bybit error codes to UTI exceptions
                ret_msg = data.get("retMsg", "Unknown error")
                logger.warning(
                    "Bybit API error — code=%s msg=%s attempt=%d",
                    ret_code,
                    ret_msg,
                    attempt,
                )
                self._raise_for_code(ret_code, ret_msg, data)

            except aiohttp.ClientError as exc:
                logger.error("HTTP error on attempt %d: %s", attempt, exc)
                if attempt == _MAX_RETRIES:
                    raise ConnectionError(
                        message=f"Failed to reach Bybit API after {_MAX_RETRIES} attempts: {exc}"
                    ) from exc
                await asyncio.sleep(_RETRY_BACKOFF * (2 ** (attempt - 1)))

        # Should not reach here, but just in case
        raise ConnectionError(message="Exhausted retries to Bybit API.")

    @staticmethod
    def _raise_for_code(
        code: int, msg: str, raw: dict[str, Any]
    ) -> None:
        """Translate a Bybit retCode into the appropriate UTI exception."""
        if code in (10003, 10004, 10005, 33004):
            raise AuthenticationError(message=msg, code=str(code), raw=raw)
        if code in (110007, 110012, 110045):
            raise InsufficientFundsError(message=msg, code=str(code), raw=raw)
        if code in (110001, 20001):
            raise OrderNotFoundError(message=msg, code=str(code), raw=raw)
        if code in (110003, 110004, 110005, 110006, 110008, 110009, 110010):
            raise InvalidOrderError(message=msg, code=str(code), raw=raw)
        if code in (10006, 10018):
            raise RateLimitError(message=msg, code=str(code), raw=raw)
        raise ExchangeError(message=msg, code=str(code), raw=raw)

    # ------------------------------------------------------------------
    # UTI Implementation — Order Management
    # ------------------------------------------------------------------

    async def place_order(self, spec: OrderSpec) -> OrderResponse:
        """Place a new order on Bybit."""
        body: dict[str, Any] = {
            "category": self.category,
            "symbol": spec.symbol,
            "side": spec.side.capitalize(),
            "orderType": spec.order_type.capitalize() if spec.order_type == "market" else "Limit",
            "qty": str(spec.qty),
        }
        if spec.price is not None:
            body["price"] = str(spec.price)
        if spec.time_in_force:
            tif_map = {"gtc": "GTC", "ioc": "IOC", "fok": "FOK", "post_only": "PostOnly"}
            body["timeInForce"] = tif_map.get(spec.time_in_force, spec.time_in_force)
        else:
            body["timeInForce"] = "GTC" if spec.order_type != "market" else "IOC"
        if spec.take_profit is not None:
            body["takeProfit"] = str(spec.take_profit)
        if spec.stop_loss is not None:
            body["stopLoss"] = str(spec.stop_loss)
        if spec.reduce_only:
            body["reduceOnly"] = True
        if spec.params:
            body.update(spec.params)

        logger.info("Placing order — %s %s %s qty=%s", spec.side, spec.order_type, spec.symbol, spec.qty)
        result = await self._request("POST", "/v5/order/create", body=body, signed=True)

        return OrderResponse(
            order_id=result.get("orderId", ""),
            symbol=spec.symbol,
            side=spec.side,
            order_type=spec.order_type,
            qty=spec.qty,
            status="new",
            raw=result,
        )

    async def cancel_order(self, symbol: str, order_id: str) -> OrderResponse:
        """Cancel an existing order on Bybit."""
        body = {
            "category": self.category,
            "symbol": symbol,
            "orderId": order_id,
        }
        logger.info("Cancelling order — symbol=%s order_id=%s", symbol, order_id)
        result = await self._request("POST", "/v5/order/cancel", body=body, signed=True)

        return OrderResponse(
            order_id=result.get("orderId", order_id),
            symbol=symbol,
            side="",
            order_type="",
            qty=0.0,
            status="cancelled",
            raw=result,
        )

    async def get_order(self, symbol: str, order_id: str) -> OrderResponse:
        """Retrieve details of a specific order."""
        params = {
            "category": self.category,
            "symbol": symbol,
            "orderId": order_id,
        }
        result = await self._request("GET", "/v5/order/realtime", params=params, signed=True)
        orders = result.get("list", [])
        if not orders:
            raise OrderNotFoundError(message=f"Order {order_id} not found for {symbol}.")

        o = orders[0]
        return OrderResponse(
            order_id=o.get("orderId", order_id),
            symbol=o.get("symbol", symbol),
            side=o.get("side", "").lower(),
            order_type=o.get("orderType", "").lower(),
            qty=float(o.get("qty", 0)),
            filled_qty=float(o.get("cumExecQty", 0)),
            price=float(o["price"]) if o.get("price") else None,
            avg_fill_price=float(o["avgPrice"]) if o.get("avgPrice") else None,
            status=o.get("orderStatus", "").lower(),
            timestamp=int(o["createdTime"]) if o.get("createdTime") else None,
            raw=o,
        )

    async def get_open_orders(
        self, symbol: str | None = None
    ) -> list[OrderResponse]:
        """Retrieve all open orders, optionally filtered by symbol."""
        params: dict[str, Any] = {"category": self.category}
        if symbol:
            params["symbol"] = symbol

        result = await self._request("GET", "/v5/order/realtime", params=params, signed=True)
        orders = result.get("list", [])

        return [
            OrderResponse(
                order_id=o.get("orderId", ""),
                symbol=o.get("symbol", ""),
                side=o.get("side", "").lower(),
                order_type=o.get("orderType", "").lower(),
                qty=float(o.get("qty", 0)),
                filled_qty=float(o.get("cumExecQty", 0)),
                price=float(o["price"]) if o.get("price") else None,
                avg_fill_price=float(o["avgPrice"]) if o.get("avgPrice") else None,
                status=o.get("orderStatus", "").lower(),
                timestamp=int(o["createdTime"]) if o.get("createdTime") else None,
                raw=o,
            )
            for o in orders
        ]

    # ------------------------------------------------------------------
    # UTI Implementation — Account & Position
    # ------------------------------------------------------------------

    async def get_wallet_balance(self) -> BalanceData:
        """Retrieve the current wallet balance."""
        params = {"accountType": "UNIFIED"}
        result = await self._request("GET", "/v5/account/wallet-balance", params=params, signed=True)
        accounts = result.get("list", [])
        if not accounts:
            return BalanceData(total_equity=0.0, available_balance=0.0)

        acct = accounts[0]
        assets = []
        for coin in acct.get("coin", []):
            assets.append({
                "currency": coin.get("coin", ""),
                "equity": float(coin.get("equity", 0)),
                "available": float(coin.get("availableToWithdraw", 0)),
                "wallet_balance": float(coin.get("walletBalance", 0)),
                "unrealised_pnl": float(coin.get("unrealisedPnl", 0)),
            })

        return BalanceData(
            total_equity=float(acct.get("totalEquity", 0)),
            available_balance=float(acct.get("totalAvailableBalance", 0)),
            currency="USDT",
            assets=assets,
        )

    async def get_positions(
        self, symbol: str | None = None
    ) -> list[PositionData]:
        """Retrieve open positions."""
        params: dict[str, Any] = {"category": self.category}
        if symbol:
            params["symbol"] = symbol

        result = await self._request("GET", "/v5/position/list", params=params, signed=True)
        positions = result.get("list", [])

        return [
            PositionData(
                symbol=p.get("symbol", ""),
                side=p.get("side", "").lower(),
                size=float(p.get("size", 0)),
                entry_price=float(p.get("avgPrice", 0)),
                mark_price=float(p["markPrice"]) if p.get("markPrice") else None,
                unrealised_pnl=float(p["unrealisedPnl"]) if p.get("unrealisedPnl") else None,
                leverage=int(p["leverage"]) if p.get("leverage") else None,
                liquidation_price=float(p["liqPrice"]) if p.get("liqPrice") and p["liqPrice"] != "" else None,
            )
            for p in positions
            if float(p.get("size", 0)) > 0
        ]

    # ------------------------------------------------------------------
    # UTI Implementation — Market Data
    # ------------------------------------------------------------------

    async def get_ticker(self, symbol: str) -> TickerData:
        """Retrieve the latest ticker for a trading pair."""
        params = {"category": self.category, "symbol": symbol}
        result = await self._request("GET", "/v5/market/tickers", params=params)
        tickers = result.get("list", [])
        if not tickers:
            raise ExchangeError(message=f"No ticker data for {symbol}.")

        t = tickers[0]
        return TickerData(
            symbol=t.get("symbol", symbol),
            last_price=float(t.get("lastPrice", 0)),
            bid=float(t["bid1Price"]) if t.get("bid1Price") else None,
            ask=float(t["ask1Price"]) if t.get("ask1Price") else None,
            high_24h=float(t["highPrice24h"]) if t.get("highPrice24h") else None,
            low_24h=float(t["lowPrice24h"]) if t.get("lowPrice24h") else None,
            volume_24h=float(t["volume24h"]) if t.get("volume24h") else None,
        )

    async def get_orderbook(
        self, symbol: str, depth: int = 25
    ) -> OrderBookData:
        """Retrieve the current order book."""
        params = {"category": self.category, "symbol": symbol, "limit": depth}
        result = await self._request("GET", "/v5/market/orderbook", params=params)

        bids = [OrderBookEntry(price=float(b[0]), qty=float(b[1])) for b in result.get("b", [])]
        asks = [OrderBookEntry(price=float(a[0]), qty=float(a[1])) for a in result.get("a", [])]

        return OrderBookData(
            symbol=symbol,
            bids=bids,
            asks=asks,
            timestamp=int(result["ts"]) if result.get("ts") else None,
        )

    async def get_candles(
        self,
        symbol: str,
        interval: str = "1",
        limit: int = 200,
    ) -> list[CandleData]:
        """Retrieve historical OHLCV candlestick data."""
        # Map common interval strings to Bybit format
        interval_map = {
            "1m": "1", "3m": "3", "5m": "5", "15m": "15", "30m": "30",
            "1h": "60", "2h": "120", "4h": "240", "6h": "360", "12h": "720",
            "1d": "D", "1w": "W", "1M": "M",
        }
        bybit_interval = interval_map.get(interval, interval)

        params = {
            "category": self.category,
            "symbol": symbol,
            "interval": bybit_interval,
            "limit": limit,
        }
        result = await self._request("GET", "/v5/market/kline", params=params)
        candles_raw = result.get("list", [])

        # Bybit returns candles newest-first; we reverse to ascending order
        candles = []
        for c in reversed(candles_raw):
            candles.append(
                CandleData(
                    timestamp=int(c[0]),
                    open=float(c[1]),
                    high=float(c[2]),
                    low=float(c[3]),
                    close=float(c[4]),
                    volume=float(c[5]),
                )
            )
        return candles

    # ------------------------------------------------------------------
    # UTI Implementation — Connectivity
    # ------------------------------------------------------------------

    async def ping(self) -> bool:
        """Health-check the connection to the Bybit API."""
        try:
            session = await self._get_session()
            async with session.get(f"{self._base_url}/v5/market/time") as resp:
                data = await resp.json()
                return data.get("retCode") == 0
        except Exception as exc:
            logger.warning("Ping failed: %s", exc)
            return False

    async def get_exchange_info(self) -> dict[str, Any]:
        """Retrieve exchange metadata for the current category."""
        params = {"category": self.category}
        result = await self._request("GET", "/v5/market/instruments-info", params=params)
        return result

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP session. Call this when you're done."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("BybitConnector session closed.")
