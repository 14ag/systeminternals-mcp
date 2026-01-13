import asyncio
from asyncio.subprocess import PIPE
from typing import List


async def run_command(exe: str, args: List[str], timeout: int = 30) -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(exe, *args, stdout=PIPE, stderr=PIPE)
    except FileNotFoundError as e:
        return {"exit_code": None, "stdout": "", "stderr": str(e), "error": "not_found", "timeout": False, "success": False}

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return {"exit_code": None, "stdout": "", "stderr": "Timed out", "timeout": True, "success": False}
    out = stdout.decode(errors="ignore") if stdout else ""
    err = stderr.decode(errors="ignore") if stderr else ""
    return {
        "exit_code": proc.returncode,
        "stdout": out,
        "stderr": err,
        "timeout": False,
        "success": (proc.returncode == 0),
    }
