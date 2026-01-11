import re
import shlex
import json
from pathlib import Path
from jsonschema import validate, ValidationError

_UNSAFE = re.compile(r"[;&|<>`$]")


def sanitize_args(args: str):
    if not args:
        return []
    if _UNSAFE.search(args):
        raise ValueError("unsafe characters detected in args")
    return shlex.split(args)


def validate_args_with_schema(tool_name: str, args: str) -> None:
    """Validate `args` against a full JSON Schema `schemas/{tool_name}.schema.json` if present.

    The schema expects an object {flags: [...], positional: [...]}. We translate
    the provided `args` into that form and run `jsonschema.validate`.
    Raises ValueError on invalid args.
    """
    p = Path("schemas") / f"{tool_name}.schema.json"
    if not p.exists():
        return
    try:
        schema = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return

    tokens = shlex.split(args) if args else []
    flags = [t for t in tokens if t.startswith("-") or t.startswith("/")]
    positional = [t for t in tokens if not (t.startswith("-") or t.startswith("/"))]

    payload = {"flags": flags, "positional": positional}
    try:
        validate(payload, schema)
    except ValidationError as e:
        raise ValueError(str(e))

