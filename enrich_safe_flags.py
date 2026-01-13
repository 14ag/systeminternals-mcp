"""Enrich `binaries.json` by probing executables for help output and generating
per-tool JSON Schemas in `schemas/`.

This script is conservative: it skips tools marked destructive in `binaries.json`
unless you set `PROBE_DESTRUCTIVE=1` environment variable.
"""
import json
import re
import subprocess
import sys
import logging
from pathlib import Path

LOG = logging.getLogger("enrich_safe_flags")

HELP_FLAGS = ["/?," ,"-?","--help","/help","-h","/?"]
FLAG_RE = re.compile(r"(?P<flag>(?:/|-{1,2})[A-Za-z0-9][-A-Za-z0-9]*)")


def probe_help(exe: Path, timeout: int = 3) -> str:
    """Probe an executable for help output in a conservative, low-risk way.

    Safety measures:
    - Only invoke common help flags ("/?, -?, --help, /help, -h").
    - Do NOT execute the binary without a help flag (no bare runs).
    - Run the subprocess with a minimal environment and hidden window on Windows.
    - Timeout quickly.
    Note: For absolute isolation, run this script inside a disposable VM/container.
    """
    # Prepare a minimal environment (preserve PATH so exe can be found)
    safe_env = {"PATH": subprocess.os.environ.get("PATH", "")}

    # Windows: hide the window when spawning
    creationflags = 0
    startupinfo = None
    if subprocess.os.name == "nt":
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        except Exception:
            startupinfo = None

    help_flags = ["/?", "-?", "--help", "/help", "-h"]
    for hf in help_flags:
        try:
            res = subprocess.run([str(exe), hf], capture_output=True, text=True, timeout=timeout,
                                 env=safe_env, cwd=subprocess.os.getcwd(), startupinfo=startupinfo,
                                 creationflags=creationflags)
        except Exception:
            continue
        out = (res.stdout or "") + (res.stderr or "")
        if out and len(out) > 10:
            return out

    return ""


def extract_flags(help_text: str):
    return sorted({m.group("flag") for m in FLAG_RE.finditer(help_text)})


def make_schema(tool_name: str, flags, allow_free: bool):
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "flags": {"type": "array", "items": {"enum": flags}},
            "positional": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": False,
    }
    if not allow_free:
        schema["properties"]["positional"]["maxItems"] = 0
    return schema


def main():
    base = Path("binaries.json")
    if not base.exists():
        LOG.error("binaries.json not found; run generate_binaries.py first")
        sys.exit(1)

    entries = json.loads(base.read_text(encoding="utf-8"))
    schemas_dir = Path("schemas")
    schemas_dir.mkdir(exist_ok=True)

    probe_destructive = (os.getenv("PROBE_DESTRUCTIVE", "0") in ("1", "true", "yes"))
    count = 0
    for e in entries:
        name = e.get("name")
        exe = e.get("exe")
        destructive = bool(e.get("destructive", False))
        if destructive and not probe_destructive:
            continue
        exe_path = Path(exe)
        if not exe_path.exists():
            # try relative
            exe_path = Path.cwd() / exe
        if not exe_path.exists():
            continue

        help_text = probe_help(exe_path)
        flags = extract_flags(help_text)
        # heurstic: allow free args unless help indicates only flags
        allow_free = True
        schema = make_schema(name, flags, allow_free)
        (schemas_dir / f"{name}.schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
        e["safe_flags"] = flags
        count += 1

    base.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    LOG.info("Updated binaries.json and generated %d schemas", count)


if __name__ == "__main__":
    import os
    main()
