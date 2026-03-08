# MCP Foundry for Trading — MCP Server
# Created for the MCP Foundry project
#
# This server exposes the Universal Trading Interface to AI agents via a
# REST API that follows MCP conventions. Any agent — Claude, GPT, LangChain,
# or your own — can call these endpoints to trade on any supported exchange.

"""
MCP Server
===========

A FastAPI-based server that bridges AI agents and financial markets through
the Universal Trading Interface. It translates HTTP/JSON requests into UTI
calls and returns structured responses that agents can reason about.

**Why FastAPI?**

We chose FastAPI because it gives us automatic OpenAPI docs, Pydantic
validation, and async support out of the box. This means any AI agent with
HTTP access can discover and use the trading tools without custom SDKs.

**Running the server:**

.. code-block:: bash

    # Using the helper script
    python scripts/run_server.py

    # Or directly with uvicorn
    uvicorn core.mcp_server:app --host 0.0.0.0 --port 8000

Then visit ``http://localhost:8000/docs`` for the interactive API explorer.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager, suppress
from typing import Any

from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from connectors import get_connector
from core.exceptions import UTIError
from core.interface import OrderSpec
from core.risk_management import RiskConfig, RiskManager
from core.trading_engine import TradingEngine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EXCHANGE = os.getenv("MCP_EXCHANGE", "bybit")
API_KEY = os.getenv("EXCHANGE_API_KEY", "")
API_SECRET = os.getenv("EXCHANGE_API_SECRET", "")
TESTNET = os.getenv("EXCHANGE_TESTNET", "true").lower() == "true"
SERVER_API_KEY = os.getenv("MCP_SERVER_API_KEY", "")  # optional auth for the server itself

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class PlaceOrderRequest(BaseModel):
    """Request body for placing an order."""
    symbol: str = Field(..., description="Trading pair, e.g. BTCUSDT")
    side: str = Field(..., description="buy or sell")
    qty: float = Field(..., gt=0, description="Quantity in base asset")
    order_type: str = Field("market", description="market or limit")
    price: float | None = Field(None, description="Limit price (required for limit orders)")
    take_profit: float | None = Field(None, description="Take-profit trigger price")
    stop_loss: float | None = Field(None, description="Stop-loss trigger price")
    time_in_force: str | None = Field(None, description="gtc, ioc, fok, or post_only")
    reduce_only: bool = Field(False, description="Reduce-only order")


class CancelOrderRequest(BaseModel):
    """Request body for cancelling an order."""
    symbol: str
    order_id: str


class SymbolRequest(BaseModel):
    """Request body for symbol-specific queries."""
    symbol: str


class OrderQueryRequest(BaseModel):
    """Request body for querying a specific order."""
    symbol: str
    order_id: str


class PositionSizeRequest(BaseModel):
    """Request body for position-size calculation."""
    symbol: str
    side: str
    entry_price: float
    stop_loss_price: float


class HealthResponse(BaseModel):
    """Server health check response."""
    status: str
    exchange: str
    testnet: bool
    connected: bool


class ToolDefinition(BaseModel):
    """MCP-style tool definition for agent discovery."""
    name: str
    description: str
    parameters: dict[str, Any]


# ---------------------------------------------------------------------------
# Application Lifecycle
# ---------------------------------------------------------------------------

connector_instance = None
engine_instance = None
risk_instance = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise connector, engine, and risk manager on startup."""
    global connector_instance, engine_instance, risk_instance

    connector_cls = get_connector(EXCHANGE)
    connector_instance = connector_cls(
        api_key=API_KEY,
        api_secret=API_SECRET,
        testnet=TESTNET,
    )
    engine_instance = TradingEngine(connector_instance)
    risk_instance = RiskManager(connector_instance, RiskConfig())

    logger.info("MCP Server started — exchange=%s testnet=%s", EXCHANGE, TESTNET)
    yield

    # Cleanup
    if hasattr(connector_instance, "close"):
        await connector_instance.close()
    logger.info("MCP Server shut down.")


app = FastAPI(
    title="MCP Foundry — Trading Server",
    description=(
        "The Universal Trading Interface (UTI) exposed as an MCP-compatible "
        "REST API. Connect any AI agent to any supported exchange."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Optional API Key Authentication
# ---------------------------------------------------------------------------

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str | None = Security(api_key_header)) -> str | None:
    """Verify the server API key if one is configured."""
    if not SERVER_API_KEY:
        return None  # No auth required
    if api_key != SERVER_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key.")
    return api_key


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _handle_uti_error(exc: UTIError) -> None:
    """Translate a UTI exception into an HTTP error."""
    from core.exceptions import (
        AuthenticationError,
        InsufficientFundsError,
        InvalidOrderError,
        OrderNotFoundError,
        RateLimitError,
    )

    status_map = {
        AuthenticationError: 401,
        InsufficientFundsError: 422,
        InvalidOrderError: 400,
        OrderNotFoundError: 404,
        RateLimitError: 429,
    }
    status = status_map.get(type(exc), 500)
    raise HTTPException(status_code=status, detail=exc.message)


# ---------------------------------------------------------------------------
# MCP Tool Discovery
# ---------------------------------------------------------------------------

@app.get("/tools", response_model=list[ToolDefinition], tags=["MCP"])
async def list_tools():
    """
    Return the list of available trading tools in MCP format.

    AI agents call this endpoint first to discover what actions are available.
    """
    return [
        ToolDefinition(
            name="place_order",
            description="Place a buy or sell order on the exchange.",
            parameters=PlaceOrderRequest.model_json_schema(),
        ),
        ToolDefinition(
            name="cancel_order",
            description="Cancel an existing open order.",
            parameters=CancelOrderRequest.model_json_schema(),
        ),
        ToolDefinition(
            name="get_balance",
            description="Get current wallet balance and equity.",
            parameters={},
        ),
        ToolDefinition(
            name="get_positions",
            description="Get all open positions.",
            parameters={},
        ),
        ToolDefinition(
            name="get_ticker",
            description="Get the latest price for a trading pair.",
            parameters=SymbolRequest.model_json_schema(),
        ),
        ToolDefinition(
            name="get_orderbook",
            description="Get the current order book for a trading pair.",
            parameters=SymbolRequest.model_json_schema(),
        ),
        ToolDefinition(
            name="get_account_summary",
            description="Get a summary of account balance and open positions.",
            parameters={},
        ),
        ToolDefinition(
            name="calculate_position_size",
            description="Calculate risk-adjusted position size given entry and stop-loss.",
            parameters=PositionSizeRequest.model_json_schema(),
        ),
    ]


# ---------------------------------------------------------------------------
# Trading Endpoints
# ---------------------------------------------------------------------------

@app.post("/trade/place_order", tags=["Trading"])
async def place_order(req: PlaceOrderRequest):
    """Place a new order through the UTI."""
    try:
        # Run risk validation first
        await risk_instance.validate_trade(req.symbol, req.side, req.qty, req.price)

        spec = OrderSpec(
            symbol=req.symbol,
            side=req.side,
            qty=req.qty,
            order_type=req.order_type,
            price=req.price,
            take_profit=req.take_profit,
            stop_loss=req.stop_loss,
            time_in_force=req.time_in_force,
            reduce_only=req.reduce_only,
        )
        result = await connector_instance.place_order(spec)
        return {
            "status": "success",
            "order_id": result.order_id,
            "symbol": result.symbol,
            "side": result.side,
            "qty": result.qty,
            "order_status": result.status,
        }
    except UTIError as exc:
        _handle_uti_error(exc)


@app.post("/trade/cancel_order", tags=["Trading"])
async def cancel_order(req: CancelOrderRequest):
    """Cancel an existing order."""
    try:
        result = await connector_instance.cancel_order(req.symbol, req.order_id)
        return {"status": "cancelled", "order_id": result.order_id}
    except UTIError as exc:
        _handle_uti_error(exc)


@app.post("/trade/close_position", tags=["Trading"])
async def close_position(req: SymbolRequest):
    """Close the entire position for a symbol."""
    try:
        result = await engine_instance.close_position(req.symbol)
        if result is None:
            return {"status": "no_position", "symbol": req.symbol}
        return {"status": "closed", "order_id": result.order_id}
    except UTIError as exc:
        _handle_uti_error(exc)


# ---------------------------------------------------------------------------
# Account Endpoints
# ---------------------------------------------------------------------------

@app.get("/account/balance", tags=["Account"])
async def get_balance():
    """Get current wallet balance."""
    try:
        balance = await connector_instance.get_wallet_balance()
        return {
            "total_equity": balance.total_equity,
            "available_balance": balance.available_balance,
            "currency": balance.currency,
            "assets": balance.assets,
        }
    except UTIError as exc:
        _handle_uti_error(exc)


@app.get("/account/positions", tags=["Account"])
async def get_positions():
    """Get all open positions."""
    try:
        positions = await connector_instance.get_positions()
        return [
            {
                "symbol": p.symbol,
                "side": p.side,
                "size": p.size,
                "entry_price": p.entry_price,
                "mark_price": p.mark_price,
                "unrealised_pnl": p.unrealised_pnl,
                "leverage": p.leverage,
            }
            for p in positions
        ]
    except UTIError as exc:
        _handle_uti_error(exc)


@app.get("/account/summary", tags=["Account"])
async def get_account_summary():
    """Get a combined summary of balance and positions."""
    try:
        return await engine_instance.get_account_summary()
    except UTIError as exc:
        _handle_uti_error(exc)


# ---------------------------------------------------------------------------
# Market Data Endpoints
# ---------------------------------------------------------------------------

@app.get("/market/ticker/{symbol}", tags=["Market Data"])
async def get_ticker(symbol: str):
    """Get the latest ticker for a symbol."""
    try:
        ticker = await connector_instance.get_ticker(symbol)
        return {
            "symbol": ticker.symbol,
            "last_price": ticker.last_price,
            "bid": ticker.bid,
            "ask": ticker.ask,
            "high_24h": ticker.high_24h,
            "low_24h": ticker.low_24h,
            "volume_24h": ticker.volume_24h,
        }
    except UTIError as exc:
        _handle_uti_error(exc)


@app.get("/market/orderbook/{symbol}", tags=["Market Data"])
async def get_orderbook(symbol: str, depth: int = 25):
    """Get the order book for a symbol."""
    try:
        ob = await connector_instance.get_orderbook(symbol, depth=depth)
        return {
            "symbol": ob.symbol,
            "bids": [{"price": b.price, "qty": b.qty} for b in ob.bids],
            "asks": [{"price": a.price, "qty": a.qty} for a in ob.asks],
        }
    except UTIError as exc:
        _handle_uti_error(exc)


@app.get("/market/candles/{symbol}", tags=["Market Data"])
async def get_candles(symbol: str, interval: str = "5m", limit: int = 100):
    """Get historical candles for a symbol."""
    try:
        candles = await connector_instance.get_candles(symbol, interval=interval, limit=limit)
        return [
            {"timestamp": c.timestamp, "open": c.open, "high": c.high, "low": c.low, "close": c.close, "volume": c.volume}
            for c in candles
        ]
    except UTIError as exc:
        _handle_uti_error(exc)


@app.get("/market/snapshot/{symbol}", tags=["Market Data"])
async def get_market_snapshot(symbol: str):
    """Get a quick market snapshot including ticker and recent candles."""
    try:
        return await engine_instance.get_market_snapshot(symbol)
    except UTIError as exc:
        _handle_uti_error(exc)


# ---------------------------------------------------------------------------
# Risk Endpoints
# ---------------------------------------------------------------------------

@app.post("/risk/position_size", tags=["Risk"])
async def calculate_position_size(req: PositionSizeRequest):
    """Calculate risk-adjusted position size."""
    try:
        size = await risk_instance.calculate_position_size(
            req.symbol, req.side, req.entry_price, req.stop_loss_price
        )
        return {"symbol": req.symbol, "side": req.side, "recommended_qty": size}
    except UTIError as exc:
        _handle_uti_error(exc)


@app.post("/risk/validate", tags=["Risk"])
async def validate_trade(req: PlaceOrderRequest):
    """Validate a proposed trade against risk rules without executing it."""
    try:
        await risk_instance.validate_trade(req.symbol, req.side, req.qty, req.price)
        return {"status": "valid", "message": "Trade passes all risk checks."}
    except UTIError as exc:
        _handle_uti_error(exc)


# ---------------------------------------------------------------------------
# Health & Info
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check if the server and exchange connection are healthy."""
    connected = False
    with suppress(Exception):
        connected = await connector_instance.ping()
    return HealthResponse(
        status="ok" if connected else "degraded",
        exchange=EXCHANGE,
        testnet=TESTNET,
        connected=connected,
    )


@app.get("/info", tags=["System"])
async def server_info():
    """Return server metadata and available connectors."""
    from connectors import list_connectors
    return {
        "project": "MCP Foundry for Trading",
        "version": "0.1.0",
        "uti_version": "0.1.0",
        "active_exchange": EXCHANGE,
        "testnet": TESTNET,
        "available_connectors": list(list_connectors().keys()),
    }
