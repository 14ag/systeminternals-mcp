Below is a **comprehensive, implementation-grade prompt** you can give directly to your AI coding agents. It is written as an internal engineering task specification, not a chatty instruction, and it explicitly covers **STDIO hygiene**, **FastMCP configuration**, and **CLI-managed auto-startup**, so the MCP server behaves like mature MCP servers that are spawned automatically by the client.

---

## Prompt for AI Coding Agents

### Role

You are a senior software engineer tasked with making an MCP server fully compliant with **STDIO-based MCP clients** and **CLI-managed lifecycle expectations**. The server must be spawnable automatically by MCP clients without manual startup and must pass discovery reliably.

---

## Objective

Fix the `systeminternals-mcp` server so that:

1. **STDOUT emits ONLY valid MCP JSON frames**
2. **ALL human-readable output is redirected to STDERR**
3. **No banners, ASCII art, logs, or prints appear on STDOUT**
4. The server **starts automatically when invoked by an MCP client**
5. The server behaves like other production MCP servers (zero manual steps)

---

## Non-Negotiable MCP Rules (Critical)

* STDOUT **must never** contain:

  * ASCII banners
  * Logging output
  * `print()` statements
  * Tool registration messages
* STDERR **is allowed** for logs and diagnostics
* Violating this breaks MCP discovery and causes:

  ```
  Client is not connected, must connect before interacting
  ```

---

## Required Changes (Implement All)

### 1. Disable FastMCP Banner and STDOUT Logging

Ensure FastMCP never writes banners or logs to STDOUT.

Implement **both**:

* Environment variable support
* Code-level safety fallback

#### Environment variables (must be respected):

* `FASTMCP_NO_BANNER=1`
* `FASTMCP_LOG_STDOUT=0`

If FastMCP does not fully respect these, enforce silence at runtime.

---

### 2. Force ALL Logging to STDERR

Audit **every logging configuration**.

If any code uses:

```python
logging.basicConfig(...)
```

Replace it with:

```python
import sys
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr
)
```

Ensure:

* Tool registration logs
* Worker startup logs
* Warnings
* Errors

All go to **STDERR only**.

---

### 3. Eliminate Accidental STDOUT Writes

Perform a repo-wide audit and fix:

* `print()`
* `rich.print()`
* banner utilities
* CLI status messages
* debug output

Replace with:

* `logging.info(...)` (stderr)
* or explicit `file=sys.stderr`

No exceptions.

---

### 4. Silence FastMCP ASCII Banner Explicitly

If FastMCP prints banners automatically:

* Disable via config if supported
* Otherwise, monkey-patch or override the banner output
* As a last resort, wrap server startup with a temporary STDOUT redirect **until MCP transport is initialized**

STDOUT must be pristine **before the MCP handshake**.

---

### 5. Ensure MCP-Only STDOUT at Runtime

Add a safety guard early in `server_mcp.py`:

* Assert STDOUT is reserved exclusively for MCP transport
* Optionally log a warning to STDERR if any non-JSON output is attempted

---

### 6. CLI-Managed Auto-Startup (No Manual Run)

The server **must not require**:

```
python server_mcp.py
```

Instead, it must be launchable automatically by MCP clients.

Implement the following:

#### A. Single Entry Point

* `server_mcp.py` must:

  * Detect MCP mode
  * Immediately start MCP stdio transport
  * Never wait for user input

#### B. No Blocking CLI Prompts

Remove or disable:

* Interactive prompts
* Demo modes
* Conditional startup paths that require flags

MCP clients expect:

> spawn → handshake → discovery

---

### 7. MCP Client Compatibility

Ensure compatibility with:

* VS Code MCP extensions
* Cursor
* Continue
* Claude MCP
* Any stdio-based MCP launcher

This means:

* No delayed banners
* No progress output
* No startup prints

---

## Validation Checklist (Must Pass)

After changes:

1. Running:

   ```
   python server_mcp.py > out.txt
   ```

   `out.txt` must be **empty**

2. STDERR must still show logs:

   ```
   python server_mcp.py 2> err.txt
   ```

3. MCP client must:

   * Discover tools successfully
   * Never throw “client not connected”
   * Not require manual startup

4. Server must stay alive until client terminates it.

---

## Deliverables

* Modified `server_mcp.py`
* Any logging/config changes required
* Optional README note explaining MCP STDIO constraints

---

## Constraints

* Do NOT change tool functionality
* Do NOT refactor business logic
* Fix only MCP lifecycle, IO hygiene, and startup behavior
* Prefer minimal, surgical changes

---

## Success Definition

The MCP server behaves identically to mature MCP servers:

* Spawned automatically
* Silent STDOUT
* Clean discovery
* No manual intervention
* Reliable across MCP clients

