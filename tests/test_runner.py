import sys
import asyncio
import json
from pathlib import Path

import pytest

from runner import run_command


def test_run_python_print():
    exe = sys.executable
    coro = run_command(exe, ["-c", "print('hello-test')"], timeout=5)
    res = asyncio.run(coro)
    assert res["exit_code"] == 0
    assert "hello-test" in res["stdout"]
