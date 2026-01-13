"""Scan the `binaries` folder and generate an enriched `binaries.json`.

This creates entries with: name, exe (relative path), category, description,
tags, destructive (bool).
"""
from pathlib import Path
import json
import sys
import logging

LOG = logging.getLogger("generate_binaries")


DESTRUCTIVE_KEYWORDS = {"sdelete", "psexec", "pskill", "format", "cipher", "psshutdown"}


def categorize(path: Path) -> str:
    low = str(path).lower()
    if "systeminternals" in low:
        return "sysinternals"
    if "nirsoft" in low:
        return "nirsoft"
    return "other"


def is_destructive(name: str) -> bool:
    n = name.lower()
    return any(k in n for k in DESTRUCTIVE_KEYWORDS)


def build_entry(p: Path, root: Path) -> dict:
    # store path relative to the project root for portability
    try:
        rel = str(p.relative_to(root))
    except Exception:
        rel = str(p)
    name = p.stem
    cat = categorize(p)
    return {
        "name": name,
        "exe": rel.replace("/", "\\"),
        "category": cat,
        "description": f"{cat} utility {name}",
        "tags": [cat],
        "destructive": is_destructive(name),
        "safe_flags": [],
    }


def main():
    base = Path("binaries")
    if not base.exists() or not base.is_dir():
        LOG.error("No `binaries` directory found.")
        sys.exit(1)

    out = []
    root = Path.cwd()
    for f in sorted(base.rglob("*.exe"), key=lambda p: str(p).lower()):
        out.append(build_entry(f, root))

    with open("binaries.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    LOG.info("Wrote binaries.json (%d entries)", len(out))


if __name__ == "__main__":
    main()
