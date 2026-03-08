# MCP Foundry for Trading — Standard Exception Hierarchy
# Created for the MCP Foundry project
#
# These exceptions form part of the UTI contract. Every connector raises
# these (and only these) exceptions so that AI agents can handle errors in a
# uniform, predictable manner regardless of the underlying exchange.

"""
UTI Standard Exception Hierarchy
=================================

All exceptions inherit from ``UTIError`` so that callers can catch the entire
family with a single ``except UTIError`` clause when broad handling is desired.

Hierarchy::

    UTIError
    ├── ConnectionError        — Network / connectivity failures
    ├── AuthenticationError    — Invalid or expired API credentials
    ├── InsufficientFundsError — Not enough margin or balance
    ├── OrderNotFoundError     — Referenced order does not exist
    ├── InvalidOrderError      — Order parameters violate exchange rules
    ├── RateLimitError         — Exchange rate limit exceeded
    └── ExchangeError          — Catch-all for exchange-side errors
"""

from __future__ import annotations

from typing import Any


class UTIError(Exception):
    """
    Base exception for all Universal Trading Interface errors.

    Attributes:
        message: Human-readable error description.
        code: Optional exchange-specific error code.
        raw: Optional raw response from the exchange for debugging.
    """

    def __init__(
        self,
        message: str = "An error occurred in the trading interface.",
        code: str | None = None,
        raw: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.raw = raw or {}
        super().__init__(self.message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"


class ConnectionError(UTIError):
    """Raised when the connector cannot reach the exchange API."""

    def __init__(
        self,
        message: str = "Failed to connect to the exchange API.",
        **kwargs: Any,
    ) -> None:
        super().__init__(message=message, **kwargs)


class AuthenticationError(UTIError):
    """Raised when API credentials are invalid, expired, or lack permissions."""

    def __init__(
        self,
        message: str = "Authentication failed. Check your API key and secret.",
        **kwargs: Any,
    ) -> None:
        super().__init__(message=message, **kwargs)


class InsufficientFundsError(UTIError):
    """Raised when the account does not have enough balance or margin."""

    def __init__(
        self,
        message: str = "Insufficient funds to execute this operation.",
        **kwargs: Any,
    ) -> None:
        super().__init__(message=message, **kwargs)


class OrderNotFoundError(UTIError):
    """Raised when a referenced order ID does not exist on the exchange."""

    def __init__(
        self,
        message: str = "The specified order was not found.",
        **kwargs: Any,
    ) -> None:
        super().__init__(message=message, **kwargs)


class InvalidOrderError(UTIError):
    """Raised when order parameters violate exchange rules (e.g., invalid qty)."""

    def __init__(
        self,
        message: str = "Invalid order parameters.",
        **kwargs: Any,
    ) -> None:
        super().__init__(message=message, **kwargs)


class RateLimitError(UTIError):
    """Raised when the exchange rate limit has been exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please retry after a delay.",
        **kwargs: Any,
    ) -> None:
        super().__init__(message=message, **kwargs)


class ExchangeError(UTIError):
    """
    Catch-all for exchange-side errors not covered by more specific exceptions.

    Connectors should prefer a more specific exception when possible.
    """

    def __init__(
        self,
        message: str = "An exchange error occurred.",
        **kwargs: Any,
    ) -> None:
        super().__init__(message=message, **kwargs)
