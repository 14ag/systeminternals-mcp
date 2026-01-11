import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from server import load_config, load_binaries, run_tool_by_name

LOG = logging.getLogger("mcp_server")


def make_tool_fn(mcp: FastMCP, entry: dict, cfg: dict):
    name = entry.get("name")

    @mcp.tool(name=name, description=f"{entry.get('category')} tool: {entry.get('exe')}")
    async def _tool(args: str = "") -> Any:
        res = await run_tool_by_name(name, args, cfg)
        return res

    return _tool


def build_mcp(cfg_path: str = "config.ini", bins_path: str = "binaries.json") -> FastMCP:
    cfg = load_config(cfg_path)
    bins = load_binaries(bins_path)

    mcp = FastMCP(name="systeminternals-mcp", instructions="Expose Sysinternals and NirSoft utilities")

    for entry in bins:
        try:
            make_tool_fn(mcp, entry, cfg)
            LOG.info("registered tool %s", entry.get("name"))
        except Exception as ex:
            LOG.exception("failed to register %s: %s", entry.get("name"), ex)

    return mcp


def main():
    mcp = build_mcp()
    # Run stdio MCP server (blocking)
    try:
        asyncio.run(mcp.run_stdio_async())
    except KeyboardInterrupt:
        LOG.info("mcp server stopped")


if __name__ == "__main__":
    main()
