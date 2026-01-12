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

## Setup

Prerequisites:

- Python 3.11+ (recommended) and `venv`.

Quick setup:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Running

- Run a single-tool demo (CLI):

```powershell
python server.py --demo pslist64
```

- Start the long-running MCP stdio server (for agent integration):

```powershell
python server_mcp.py
```

The `--demo` mode is useful for simple CLI usage and for coding agents that can execute shell commands and parse JSON output. `server_mcp.py` exposes the full MCP stdio endpoint for clients that implement the MCP protocol.

## Using from a CLI or a coding agent

1) Simple CLI / scripting approach (recommended for automation and agents that can run subprocesses): the `--demo` command prints JSON to stdout which is easy to parse from any language.

Example Python snippet (agent or script):

```python
import subprocess, json

proc = subprocess.run([
	'python', 'server.py', '--demo', 'pslist64', '--',
	# additional tool args go here as separate items
], capture_output=True, text=True)

if proc.returncode == 0 and proc.stdout:
	result = json.loads(proc.stdout)
	print(result)
else:
	print('error', proc.stderr)
```

Note: place any tool arguments after `--demo <toolname>`; the demo command will join remaining argv pieces for the tool.

2) Long-running MCP server (for advanced agents):

- Start the server with `python server_mcp.py` (it will register tools from `binaries.json` or the `binaries/` directory).
- Use an MCP-capable client to connect over stdio (spawn the server as a child process and implement the MCP framing). Many agent frameworks support providing a long-lived process that the agent can call into; in that case the MCP stdio server gives a stable RPC surface.

If your agent framework doesn't implement MCP natively, use the simple subprocess approach above to execute `server.py --demo` per-request.

## Security and best practices

- Never allow untrusted agents or users to run destructive tools. Destructive tools are blocked by default; confirmations are required (interactive prompt, `--confirm` or `allow_destructive=true` in `config.ini`).
- When generating per-tool schemas or probing help text, run the probe in an isolated environment (VM or disposable container) to avoid accidental execution of unsafe binaries.
- For production use, add authentication around the MCP stdio process and run under restricted privileges.

## CI

A GitHub Actions workflow is included at `.github/workflows/ci.yml` that runs the test suite on push and pull requests.

## `mcpServers` (IDE / agent integration)

If your editor/agent supports a `mcpServers` config (for example the Gemini client settings), add entries that either start the stdio MCP server or point to a running HTTP MCP endpoint.

Example — start the long-lived stdio MCP server from this repo (preferred for full MCP integration):

```json
"systeminternals-mcp": {
	"command": "python",
	"args": [
		"C:\\path\\to\\the\\server_mcp.py"
	]
}
```

Example — demo/one-shot entry that runs `--demo` and prints JSON (useful for simple agents that call subprocesses):

```json
"systeminternals-mcp-demo": {
	"command": "python",
	"args": [
		"C:\\path\\to\\the\\server.py",
		"--demo"
	]
}
```

Example — point to an existing HTTP MCP endpoint:

```json
"systeminternals-mcp-http": {
	"url": "http://127.0.0.1:12345/mcp"
}
```

Notes:

- Use absolute Windows paths (escape backslashes in JSON) or a plain `python` command if the environment activates the virtualenv automatically.
- If your client supports `cwd` and `env`, set them so the server runs in the repo root and uses the `.venv` Python.
- Prefer the stdio MCP server (`server_mcp.py`) for integrated agents; use `--demo` for simple per-request subprocess calls that return JSON.

