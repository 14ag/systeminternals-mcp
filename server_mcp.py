import os
import sys
import asyncio
import json
import logging
from pathlib import Path
from typing import Any

# Ensure FastMCP does not print banners or log to stdout. Set env vars
# before importing fastmcp so the library sees them during import/init.
os.environ.setdefault("FASTMCP_NO_BANNER", "1")
os.environ.setdefault("FASTMCP_LOG_STDOUT", "0")

# Ensure logging defaults send output to stderr
logging.basicConfig(level=logging.INFO, stream=sys.stderr)

# Protect stdout during initialization: any accidental prints go to stderr
# until we explicitly restore stdout just prior to starting the MCP transport.
_orig_stdout = sys.stdout
class _StdoutGuard:
    def __init__(self, err_stream):
        self._err = err_stream
    def write(self, s):
        if not s:
            return
        try:
            self._err.write(s)
        except Exception:
            pass
    def flush(self):
        try:
            self._err.flush()
        except Exception:
            pass

sys.stdout = _StdoutGuard(sys.stderr)

from fastmcp import FastMCP
import fastmcp as _fastmcp

from server import load_config, load_binaries, run_tool_by_name

LOG = logging.getLogger("mcp_server")


def make_tool_fn(mcp: FastMCP, entry: dict, cfg: dict):
    name = entry.get("name")

    @mcp.tool(name=name, description=f"{entry.get('category')} tool: {entry.get('exe')}")
    async def _tool(args: str = "") -> Any:
        try:
            res = await run_tool_by_name(name, args, cfg)
            return res
        except Exception as ex:
            LOG.exception("unhandled exception in tool %s", name)
            return {"error": "internal_error", "detail": str(ex)}

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
    # Run stdio MCP server (blocking). Keep stdout pristine — FastMCP
    # will use stdout for the MCP transport. Any human-readable logs
    # should go to stderr (we already configured logging above).
    # Restore real stdout so FastMCP can use it for the MCP wire protocol
    try:
        sys.stdout = _orig_stdout
    except Exception:
        pass

    # Install simple signal handlers for graceful shutdown
    import signal

    def _term_handler(signum, frame):
        LOG.info("received signal %s, exiting", signum)
        try:
            sys.exit(0)
        except SystemExit:
            raise

    try:
        signal.signal(signal.SIGINT, _term_handler)
        signal.signal(signal.SIGTERM, _term_handler)
    except Exception:
        # Some platforms may not allow signal handling; ignore
        pass

    async def _run_mcp(mcp_inst: FastMCP):
        # Prefer explicit stdio server + run(handshake) if available in FastMCP.
        stdio_server = getattr(_fastmcp, "stdio_server", None)
        run_fn = getattr(mcp_inst, "run", None)
        if stdio_server and run_fn:
            try:
                async with stdio_server() as (r, w):
                    # Try to provide InitializationOptions if available
                    Init = getattr(_fastmcp, "InitializationOptions", None)
                    if Init:
                        init_opts = Init(server_name="systeminternals-mcp")
                        await run_fn(r, w, init_opts)
                    else:
                        await run_fn(r, w)
                return
            except Exception:
                LOG.exception("explicit run(handshake) failed, falling back")

        # Fallbacks
        run_stdio = getattr(mcp_inst, "run_stdio_async", None)
        if run_stdio:
            await run_stdio()
            return

        if run_fn:
            try:
                # last resort: pass raw stdio buffers
                await run_fn(sys.stdin.buffer, sys.stdout.buffer)
                return
            except Exception:
                LOG.exception("mcp.run with raw buffers failed")

        raise RuntimeError("No compatible FastMCP run method available")

    try:
        asyncio.run(_run_mcp(mcp))
    except KeyboardInterrupt:
        LOG.info("mcp server stopped")


if __name__ == "__main__":
    main()
