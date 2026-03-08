#!/usr/bin/env python3
# MCP Foundry for Trading — Server Runner
# Created for the MCP Foundry project
#
# Quick way to start the MCP trading server.
# Usage:
#   python scripts/run_server.py
#   python scripts/run_server.py --host 0.0.0.0 --port 8000

"""
Run the MCP Foundry trading server.

This script initialises logging and starts the FastAPI server via uvicorn.
"""

from __future__ import annotations

import argparse
import os
import sys

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the MCP Foundry trading server.")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--log-level", default="info", help="Log level (default: info)")
    args = parser.parse_args()

    # Set up structured logging
    from utils.logging_config import setup_logging
    setup_logging(level=args.log_level.upper())

    import uvicorn

    print(
        f"\n  MCP Foundry — Trading Server\n"
        f"  Listening on http://{args.host}:{args.port}\n"
        f"  API docs at  http://{args.host}:{args.port}/docs\n"
    )

    uvicorn.run(
        "core.mcp_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level.lower(),
    )


if __name__ == "__main__":
    main()
