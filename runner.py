import asyncio
from asyncio.subprocess import PIPE
from typing import List


async def run_command(exe: str, args: List[str], timeout: int = 30) -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(exe, *args, stdout=PIPE, stderr=PIPE)
    except FileNotFoundError as e:
        return {"exit_code": None, "stdout": "", "stderr": str(e), "error": "not_found"}

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return {"exit_code": None, "stdout": "", "stderr": "Timed out", "timeout": True}

    return {
        "exit_code": proc.returncode,
        "stdout": stdout.decode(errors="ignore") if stdout else "",
        "stderr": stderr.decode(errors="ignore") if stderr else "",
    }
