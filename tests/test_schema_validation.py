import os
import json
import pytest
from pathlib import Path

from sanitize import validate_args_with_schema


def write_schema(name: str, schema: dict):
    p = Path("schemas")
    p.mkdir(exist_ok=True)
    (p / f"{name}.schema.json").write_text(json.dumps(schema), encoding="utf-8")


def test_validate_allowed_flag():
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "flags": {"type": "array", "items": {"enum": ["/stext", "/sxml"]}},
            "positional": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": False,
    }
    write_schema("testtool", schema)
    # allowed
    validate_args_with_schema("testtool", "/stext file.txt")


def test_reject_disallowed_flag():
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "flags": {"type": "array", "items": {"enum": ["/stext"]}},
            "positional": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": False,
    }
    write_schema("testtool2", schema)
    with pytest.raises(ValueError):
        validate_args_with_schema("testtool2", "/sxml file.txt")


def test_reject_free_args_when_not_allowed():
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "flags": {"type": "array", "items": {"enum": ["/stext"]}},
            "positional": {"type": "array", "items": {"type": "string"}, "maxItems": 0},
        },
        "additionalProperties": False,
    }
    write_schema("testtool3", schema)
    with pytest.raises(ValueError):
        validate_args_with_schema("testtool3", "/stext extra_arg")
