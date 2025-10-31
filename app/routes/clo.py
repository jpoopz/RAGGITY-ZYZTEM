from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import asyncio
import os


router = APIRouter()


async def _probe_async(host: str, port: int, timeout_s: float = 0.5) -> bool:
    try:
        await asyncio.wait_for(asyncio.open_connection(host, int(port)), timeout=timeout_s)
        return True
    except Exception:
        return False


@router.get("/clo/health")
async def clo_health(host: str = Query("127.0.0.1"), port: int | None = Query(None)):
    if port is None:
        try:
            port = int(os.getenv("CLO_BRIDGE_PORT", "9933"))
        except Exception:
            port = 9933

    ok = await _probe_async(host, port, 0.5)
    if ok:
        return JSONResponse({"ok": True})
    return JSONResponse({"ok": False, "advice": "Port unreachable or blocked"})


