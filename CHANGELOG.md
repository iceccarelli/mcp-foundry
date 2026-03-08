# Changelog

All notable changes to the MCP Foundry will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2025-03-08

### Added

- **Universal Trading Interface (UTI) v0.1.0** — Core specification with data models, enumerations, and protocol definition.
- **Bybit V5 Connector** — Production-ready reference implementation covering spot and linear perpetual futures.
- **MCP Server** — FastAPI-based REST API with tool discovery, automatic validation, and OpenAPI documentation.
- **Trading Engine** — Exchange-agnostic engine with convenience methods for market orders, limit orders, and position management.
- **Risk Management** — Configurable pre-trade risk checks including position sizing, exposure limits, and daily loss caps.
- **Connector Registry** — Dynamic connector discovery and registration system.
- **Exception Hierarchy** — Structured error handling with exchange error code translation.
- **Examples** — Basic market order, MCP server interaction, and AI agent integration demos.
- **Test Suite** — Comprehensive tests with mocked connectors for all core modules.
- **Documentation** — Architecture guide, UTI specification, connector development guide, and quick start guide.
- **Docker Support** — Dockerfile and docker-compose.yml for containerised deployment.
- **CI/CD** — GitHub Actions workflows for testing and Docker image publishing.
