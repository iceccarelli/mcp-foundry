# MCP Foundry for Trading — Tests: Connector Registry
# Created for the MCP Foundry project

"""
Tests for the connector registry and Bybit connector initialisation.
"""

from __future__ import annotations

import pytest

from connectors import get_connector, list_connectors, register_connector
from connectors.bybit import BybitConnector


class TestConnectorRegistry:
    """Test the connector discovery and registration system."""

    def test_bybit_is_registered(self) -> None:
        connectors = list_connectors()
        assert "bybit" in connectors
        assert connectors["bybit"] is BybitConnector

    def test_get_bybit_connector(self) -> None:
        cls = get_connector("bybit")
        assert cls is BybitConnector

    def test_case_insensitive_lookup(self) -> None:
        cls = get_connector("BYBIT")
        assert cls is BybitConnector

    def test_unknown_connector_raises(self) -> None:
        with pytest.raises(KeyError, match="No connector registered"):
            get_connector("nonexistent_exchange")

    def test_register_custom_connector(self) -> None:
        class FakeConnector:
            pass

        register_connector("fake", FakeConnector)
        assert get_connector("fake") is FakeConnector


class TestBybitConnectorInit:
    """Test BybitConnector initialisation (no network calls)."""

    def test_default_init(self) -> None:
        conn = BybitConnector(api_key="key", api_secret="secret")
        assert conn.api_key == "key"
        assert conn.testnet is False
        assert conn.category == "linear"

    def test_testnet_init(self) -> None:
        conn = BybitConnector(api_key="key", api_secret="secret", testnet=True)
        assert conn.testnet is True
        assert "testnet" in conn._base_url

    def test_spot_category(self) -> None:
        conn = BybitConnector(api_key="key", api_secret="secret", category="spot")
        assert conn.category == "spot"
