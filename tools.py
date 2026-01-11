import json
import logging
import os
from pathlib import Path

LOG = logging.getLogger("mcp_tools")


def register_tools_with_fastmcp(app=None, binaries_path: str = "binaries.json"):
    try:
        import fastmcp
    except Exception:
        LOG.warning("fastmcp not available; skipping dynamic registration")
        return []

    p = Path(binaries_path)
    if not p.exists():
        LOG.warning("binaries.json not found; no tools to register")
        return []

    bins = json.loads(p.read_text(encoding="utf-8"))
    registered = []

    for entry in bins:
        name = entry.get("name")
        exe = entry.get("exe")
        category = entry.get("category", "other")

        def make_tool(exe_path, category):
            @fastmcp.tool(name=name)
            def _tool(args: str = "") -> dict:
                # The actual implementation will be provided by server.run_tool_by_name
                return {"note": "proxy tool", "exe": exe_path, "category": category, "args": args}

            return _tool

        # Use the exe name as-is; runtime will resolve using config paths
        tool = make_tool(exe, category)
        registered.append(name)

    LOG.info("Registered %d tools (stub) with fastmcp", len(registered))
    return registered


if __name__ == "__main__":
    register_tools_with_fastmcp()
