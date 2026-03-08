# Hosted Gateway — Trading Infrastructure as a Service

This directory is reserved for the **MCP Foundry Hosted Gateway**, a managed cloud service that wraps the open-source core with the operational infrastructure that production teams need.

## The idea

The open-source MCP Foundry gives you everything to self-host a trading gateway. But running it in production — with uptime guarantees, secure credential management, audit trails, and low latency — takes real operational effort. The Hosted Gateway handles that for you.

## Planned capabilities

### Secure Credential Vault

Your exchange API keys never touch your application code. The gateway integrates with secrets management infrastructure (HashiCorp Vault, AWS Secrets Manager) to store, rotate, and audit credentials.

### Immutable Audit Logs

Every order, every cancellation, every balance query — logged immutably and tamper-proof. Designed to support SOC 2 Type II and PCI-DSS compliance requirements.

### Global Rate Limiting and Fair-Use Pacing

Intelligent rate limiting that respects exchange-specific limits across all tenants. No more accidental API bans.

### Low-Latency Co-location

For teams where execution speed matters, the gateway can be deployed in proximity to exchange matching engines via AWS, Equinix, and other co-location providers in key financial centres (New York, London, Tokyo, Singapore).

### High Availability

Designed for 99.99% uptime with automatic failover, health monitoring, and incident response.

### Multi-Tenant Architecture

Each team gets isolated resources, separate credentials, and independent configuration — all managed through a single control plane.

## Service tiers

| Tier | For | Highlights |
| :--- | :--- | :--- |
| **Community** | Individual developers | Self-hosted, open-source core, community support |
| **Pro** | Professional traders, small teams | Managed gateway, credential vault, priority support |
| **Enterprise** | Institutions, funds | Dedicated instance, co-location, SLA, audit logs, all enterprise add-ons |

## Current status

The Hosted Gateway is under active development. We're building it based on real feedback from teams that are already using the open-source core.

## Get involved

If you're interested in early access, or if you have specific requirements you'd like us to consider, we'd love to hear from you:

- Join the conversation in [GitHub Discussions](https://github.com/mcp-foundry/mcp-foundry/discussions)
- Email: **gateway@mcpfoundry.dev**

Your input directly shapes what we build. We're not guessing at features — we're building what you tell us you need.
