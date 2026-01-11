import asyncio
import json
import logging
import logging.config
import os
import tempfile
import sys

from pathlib import Path

from runner import run_command
from sanitize import sanitize_args

LOG = logging.getLogger("mcp_server")
conf_path = Path("logging.conf")
if conf_path.exists():
    try:
        logging.config.fileConfig(conf_path, disable_existing_loggers=False)
    except Exception:
        logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)


def load_config(path: str = "config.ini") -> dict:
    import configparser

    cfg = {}
    p = Path(path)
    if not p.exists():
        LOG.warning("config.ini not found; using defaults")
        return cfg
    parser = configparser.ConfigParser()
    parser.read(p)
    # read server section
    if parser.has_section("server"):
        cfg["LOG_LEVEL"] = parser.get("server", "log_level", fallback="INFO")
        cfg["TIMEOUT"] = parser.get("server", "timeout", fallback="30")
        cfg["ALLOW_DESTRUCTIVE"] = parser.get("server", "allow_destructive", fallback="false")
    return cfg


def load_binaries(path: str = "binaries.json") -> list:
    p = Path(path)
    # If path is a directory, scan recursively for executables
    if p.exists() and p.is_dir():
        out = []
        for f in p.rglob("*.exe"):
            rel = str(f)
            name = f.stem
            low = str(f).lower()
            if "systeminternals" in low:
                cat = "sysinternals"
            elif "nirsoft" in low:
                cat = "nirsoft"
            else:
                cat = "other"
            out.append({"name": name, "exe": rel, "category": cat})
        return out

    # If file exists and is JSON, load it
    if p.exists() and p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            LOG.warning("failed to parse binaries.json; no tools registered")
            return []

    # fallback: look for a `binaries` directory next to the script
    fallback = Path("binaries")
    if fallback.exists() and fallback.is_dir():
        return load_binaries(str(fallback))

    LOG.warning("binaries.json not found and no binaries directory; no tools registered")
    return []


async def run_tool_by_name(name: str, args: str, cfg: dict):
    bins = load_binaries()
    entry = next((b for b in bins if b.get("name") == name), None)
    if not entry:
        return {"error": "tool not found", "name": name}

    base = cfg.get("PATH_SYS") if entry.get("category") == "sysinternals" else cfg.get("PATH_X64")
    exe = entry.get("exe")
    if base:
        exe_path = os.path.join(base, exe)
    else:
        exe_path = exe

    try:
        argv = sanitize_args(args)
    except ValueError as ex:
        return {"error": "unsafe arguments", "detail": str(ex)}

    # Per-tool schema validation (if present)
    try:
        from sanitize import validate_args_with_schema
        validate_args_with_schema(entry.get("name"), args)
    except ValueError as ex:
        return {"error": "args_schema_violation", "detail": str(ex)}
    except Exception:
        pass

    # Safety check for destructive tools
    DESTRUCTIVE = {"sdelete", "sdelete64", "psexec", "psexec64", "pskill", "pskill64", "psservice", "psshutdown", "format", "cipher"}
    exe_stem = Path(exe_path).stem.lower()
    is_destructive = any(d in exe_stem for d in DESTRUCTIVE) or name.lower() in DESTRUCTIVE
    allow_flag = cfg.get("ALLOW_DESTRUCTIVE", "0").lower() in ("1", "true", "yes")
    if is_destructive and not (allow_flag or "--confirm" in args or "confirm=yes" in args):
        # If running interactively (tty), prompt the user for confirmation.
        try:
            if sys.stdin and sys.stdin.isatty():
                prompt = f"Tool '{name}' appears destructive. Type 'yes' to confirm and run: "
                resp = input(prompt)
                if resp.strip().lower() != "yes":
                    LOG.warning("user declined destructive tool %s", name)
                    return {"error": "destructive_tool_blocked", "detail": "User declined confirmation."}
                # proceed
            else:
                LOG.warning("blocked destructive tool invocation for %s (non-interactive)", name)
                return {"error": "destructive_tool_blocked", "detail": "Tool is destructive. Run with `--confirm` or enable allow_destructive=true in config.ini."}
        except Exception:
            return {"error": "destructive_tool_blocked", "detail": "Unable to prompt for confirmation. Use --confirm or set ALLOW_DESTRUCTIVE=1."}

    # Audit log the requested invocation
    audit = logging.getLogger("audit")
    audit.info("invoke", extra={
        "tool": name,
        "exe": exe_path,
        "params": args,
        "category": entry.get("category"),
    })

    # Auto flags for Sysinternals / NirSoft where appropriate
    if entry.get("category") == "sysinternals":
        argv = ["-accepteula", "-nobanner"] + argv
        res = await run_command(exe_path, argv, timeout=30)
    elif entry.get("category") == "nirsoft":
        # prefer text output into a temp file, then read it back
        if "/stext" not in args and "/sxml" not in args:
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            tf_path = tf.name
            tf.close()
            argv = ["/stext", tf_path] + argv

            res = await run_command(exe_path, argv, timeout=30)
            # if file produced, attach its contents
            try:
                with open(tf_path, "r", encoding="utf-8", errors="ignore") as f:
                    body = f.read()
                    res["stdout"] = (res.get("stdout", "") or "") + body
            except Exception:
                pass
            finally:
                try:
                    os.unlink(tf_path)
                except Exception:
                    pass
        else:
            res = await run_command(exe_path, argv, timeout=30)
    else:
        res = await run_command(exe_path, argv, timeout=30)

    audit.info("result", extra={
        "tool": name,
        "exit_code": res.get("exit_code"),
        "timeout": res.get("timeout", False),
    })
    return res


def main():
    cfg = load_config()
    if len(sys.argv) >= 3 and sys.argv[1] == "--demo":
        name = sys.argv[2]
        args = " " .join(sys.argv[3:])
        result = asyncio.run(run_tool_by_name(name, args, cfg))
        print(json.dumps(result, indent=2))
        return

    print("Minimal MCP scaffold. Use `--demo <toolname> [args]` to run a tool.")


if __name__ == "__main__":
    main()
