from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import socket
import json
import os


router = APIRouter()


def _probe_clo_tcp(host: str, port: int, timeout: float = 0.5):
    try:
        with socket.create_connection((host, int(port)), timeout=timeout) as s:
            try:
                s.sendall((json.dumps({"ping": "clo"}) + "\n").encode("utf-8"))
                s.settimeout(timeout)
                data = s.recv(4096)
                if b"pong" in data:
                    return True, "pong"
            except Exception:
                pass
            return True, "tcp_ok"
    except socket.timeout:
        return False, "timeout"
    except ConnectionRefusedError:
        return False, "refused"
    except Exception as e:
        return False, type(e).__name__


@router.get("/clo/health")
def clo_health(host: str = Query("127.0.0.1"), port: int | None = Query(None)):
    if port is None:
        try:
            port = int(os.getenv("CLO_BRIDGE_PORT", "9933"))
        except Exception:
            port = 9933

    ok, detail = _probe_clo_tcp(host, port)

    advice = ""
    if ok:
        advice = "pong" if detail == "pong" else "tcp_ok"
    else:
        if detail == "timeout":
            advice = "Listener timeout: ensure CLO script is running and firewall allows inbound on this port"
        elif detail == "refused":
            advice = "Connection refused: verify port and that CLO listener is active"
        else:
            advice = f"Error: {detail}"

    return JSONResponse({"ok": bool(ok), "advice": advice, "host": host, "port": port})


