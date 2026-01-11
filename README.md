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

Edit `config.txt` to point `PATH_X64` and `PATH_SYS` at your binary directories.

Security notes: This scaffold sanitizes arguments and uses `asyncio.create_subprocess_exec` without a shell. Extend with explicit safety filters before using in production.

Safety filter: destructive tools (for example `sdelete`, `psexec`, `pskill`) are blocked by default. To run them you must either:

- Add `--confirm` to the tool arguments, or
- Set `ALLOW_DESTRUCTIVE=1` in `config.txt`.

The server also scans a `binaries` directory recursively if present; place your tool folders (e.g., `systeminternals`, `nirsoft`) under `binaries`.
