# MCP Foundry for Trading — Tests: MCP Server
# Created for the MCP Foundry project

"""
Tests for the MCP Server API endpoints.

Uses FastAPI's TestClient for synchronous testing of the async endpoints.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(mock_connector, sample_ticker, sample_balance, sample_position, sample_order_response):
    """Create a test client with mocked connector."""
    with patch("core.mcp_server.connector_instance", mock_connector), \
         patch("core.mcp_server.engine_instance") as mock_engine, \
         patch("core.mcp_server.risk_instance") as mock_risk:

        mock_engine.get_account_summary = AsyncMock(return_value={
            "total_equity": 10000.0,
            "available_balance": 8500.0,
            "currency": "USDT",
            "open_positions": [],
        })
        mock_engine.get_market_snapshot = AsyncMock(return_value={
            "symbol": "BTCUSDT",
            "last_price": 67500.0,
            "bid": 67499.5,
            "ask": 67500.5,
            "recent_candles": [],
        })
        mock_engine.close_position = AsyncMock(return_value=sample_order_response)
        mock_risk.validate_trade = AsyncMock(return_value=True)

        from core.mcp_server import app
        yield TestClient(app, raise_server_exceptions=False)


class TestToolDiscovery:
    """Test the MCP tool discovery endpoint."""

    def test_list_tools(self, client) -> None:
        resp = client.get("/tools")
        assert resp.status_code == 200
        tools = resp.json()
        assert isinstance(tools, list)
        assert len(tools) > 0
        tool_names = [t["name"] for t in tools]
        assert "place_order" in tool_names
        assert "get_balance" in tool_names
        assert "get_ticker" in tool_names


class TestTradingEndpoints:
    """Test trading API endpoints."""

    def test_place_order(self, client) -> None:
        resp = client.post("/trade/place_order", json={
            "symbol": "BTCUSDT",
            "side": "buy",
            "qty": 0.001,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "order_id" in data

    def test_cancel_order(self, client) -> None:
        resp = client.post("/trade/cancel_order", json={
            "symbol": "BTCUSDT",
            "order_id": "test-order-001",
        })
        assert resp.status_code == 200

    def test_close_position(self, client) -> None:
        resp = client.post("/trade/close_position", json={"symbol": "BTCUSDT"})
        assert resp.status_code == 200


class TestAccountEndpoints:
    """Test account API endpoints."""

    def test_get_balance(self, client) -> None:
        resp = client.get("/account/balance")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_equity" in data

    def test_get_positions(self, client) -> None:
        resp = client.get("/account/positions")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_account_summary(self, client) -> None:
        resp = client.get("/account/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_equity" in data


class TestMarketDataEndpoints:
    """Test market data API endpoints."""

    def test_get_ticker(self, client) -> None:
        resp = client.get("/market/ticker/BTCUSDT")
        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "BTCUSDT"
        assert "last_price" in data

    def test_get_orderbook(self, client) -> None:
        resp = client.get("/market/orderbook/BTCUSDT")
        assert resp.status_code == 200
        data = resp.json()
        assert "bids" in data
        assert "asks" in data


class TestSystemEndpoints:
    """Test system endpoints."""

    def test_health_check(self, client) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "connected" in data

    def test_server_info(self, client) -> None:
        resp = client.get("/info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project"] == "MCP Foundry for Trading"
        assert "available_connectors" in data
