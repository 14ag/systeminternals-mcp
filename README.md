# systeminternals-mcp (scaffold)

Minimal FastMCP-compatible scaffold that demonstrates dynamic registration and safe subprocess wrapping for exposing Sysinternals and NirSoft binaries.

Quick demo:

```bash
python server.py --demo procexp64
```

Start the MCP stdio server:

```bash
python server_mcp.py
```

Edit `config.ini` to adjust server settings (log level, timeout, allow_destructive).
The server no longer requires explicit binary paths — it scans the `binaries/` directory recursively.

Security notes: This scaffold sanitizes arguments and uses `asyncio.create_subprocess_exec` without a shell. Extend with explicit safety filters before using in production.

Safety filter: destructive tools (for example `sdelete`, `psexec`, `pskill`) are blocked by default. To run them you must either:

- Add `--confirm` to the tool arguments, or
 - Set `allow_destructive = true` in the `[server]` section of `config.ini`.

The server also scans a `binaries` directory recursively if present; place your tool folders (e.g., `systeminternals`, `nirsoft`) under `binaries`.
