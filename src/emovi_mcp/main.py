"""MCP server entry point — STDIO transport."""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from emovi_mcp.tools import register_tools

logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s: %(message)s")


def main():
    mcp = FastMCP(
        "emovi-mcp",
        instructions=(
            "You are connected to the ESRU-EMOVI 2023 survey on social mobility "
            "in Mexico. Use the available tools to explore the data, compute "
            "weighted statistics, and generate transition matrices. Always "
            "interpret results considering the survey's expansion factors."
        ),
    )
    register_tools(mcp)
    mcp.run()


if __name__ == "__main__":
    main()
