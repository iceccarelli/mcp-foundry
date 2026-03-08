# Enterprise Add-ons

This directory is reserved for **enterprise-grade modules** that extend the MCP Foundry beyond the open-source core. These are proprietary, commercially licensed components designed for organisations with advanced requirements.

## What belongs here

### Proprietary Connectors

Production-ready integrations with systems that institutional teams rely on every day:

| Connector | Use Case |
| :--- | :--- |
| **SAP S/4HANA** | Automated trade settlement and treasury management |
| **Salesforce CRM** | Client portfolio tracking and reporting |
| **Bloomberg Terminal API** | Real-time institutional data feeds |
| **Interactive Brokers** | Multi-asset brokerage execution |
| **FIX Protocol Gateway** | Standard FIX 4.2/4.4 connectivity |

### Advanced Execution Algorithms

Institutional-grade execution modules that go beyond simple market and limit orders:

| Algorithm | Description |
| :--- | :--- |
| **VWAP** | Volume-Weighted Average Price execution |
| **TWAP** | Time-Weighted Average Price execution |
| **Smart Order Routing (SOR)** | Optimal venue selection across exchanges |
| **Iceberg Orders** | Large order slicing with configurable visibility |

### Pre-Trade Risk and Compliance

| Module | Description |
| :--- | :--- |
| **Value-at-Risk (VaR) Engine** | Real-time portfolio risk assessment |
| **Compliance Rule Engine** | Configurable pre-trade compliance checks |
| **Regulatory Reporting** | Automated MiFID II / Dodd-Frank reporting |

## Why separate?

The open-source core gives you everything you need to connect AI agents to exchanges and build trading strategies. The enterprise modules address the additional requirements that come with institutional scale — regulatory compliance, legacy system integration, and advanced execution quality.

We keep them separate so the core stays lightweight and permissively licensed, while organisations that need these capabilities have a clear path to get them.

## Interested?

If your team needs any of these capabilities, or if you have a use case we haven't listed, we'd genuinely like to hear from you. Reach out to the project maintainer:

- Open a [GitHub Discussion](https://github.com/mcp-foundry/mcp-foundry/discussions)
- Email: **enterprise@mcpfoundry.dev**

We're building this in the open because we believe the standard should belong to everyone. The enterprise layer exists to support teams that need it, and your feedback helps us prioritise what to build next.
