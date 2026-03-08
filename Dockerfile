# MCP Foundry for Trading — Docker Image
# Multi-stage build for a lean production image.

# --- Build stage ---
FROM python:3.11-slim AS builder

WORKDIR /app

COPY pyproject.toml .
COPY README.md .
COPY core/ core/
COPY connectors/ connectors/
COPY utils/ utils/
COPY enterprise/ enterprise/
COPY gateway/ gateway/
COPY scripts/ scripts/
COPY config/ config/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# --- Production stage ---
FROM python:3.11-slim

LABEL org.opencontainers.image.title="MCP Foundry for Trading"
LABEL org.opencontainers.image.description="The Universal Trading Interface — connecting AI agents to financial markets."
LABEL org.opencontainers.image.source="https://github.com/mcp-foundry/mcp-foundry"
LABEL org.opencontainers.image.licenses="Apache-2.0"

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY core/ core/
COPY connectors/ connectors/
COPY utils/ utils/
COPY enterprise/ enterprise/
COPY gateway/ gateway/
COPY scripts/ scripts/
COPY config/ config/

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Environment defaults
ENV MCP_EXCHANGE=bybit \
    EXCHANGE_TESTNET=true \
    MCP_SERVER_HOST=0.0.0.0 \
    MCP_SERVER_PORT=8000 \
    LOG_LEVEL=INFO

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "scripts/run_server.py"]
