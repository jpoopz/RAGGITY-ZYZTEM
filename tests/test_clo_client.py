import socket
import threading
import json
import time

import pytest

from modules.clo_companion.clo_client import CLOClient


def start_mock_clo_server(handler):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    stop = {"flag": False}

    def run():
        while not stop["flag"]:
            srv.settimeout(0.5)
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            with conn:
                buf = b""
                conn.settimeout(2)
                while True:
                    try:
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        buf += chunk
                        while b"\n" in buf:
                            line, buf = buf.split(b"\n", 1)
                            if not line:
                                continue
                            try:
                                req = json.loads(line.decode("utf-8"))
                            except json.JSONDecodeError:
                                # return error json
                                resp = {"success": False, "error": "Invalid JSON"}
                                conn.sendall((json.dumps(resp) + "\n").encode("utf-8"))
                                continue
                            resp = handler(req)
                            conn.sendall((json.dumps(resp) + "\n").encode("utf-8"))
                    except socket.timeout:
                        break

    th = threading.Thread(target=run, daemon=True)
    th.start()
    return port, stop, srv, th


def test_connect_and_basic_commands():
    def handler(req):
        cmd = req.get("cmd")
        if cmd == "ping":
            return {"success": True, "message": "pong"}
        if cmd == "import_garment":
            return {"success": True, "echo": req}
        if cmd == "take_screenshot":
            return {"success": True, "path": req.get("path")}
        if cmd == "run_simulation":
            steps = req.get("steps", 0)
            if steps <= 0:
                return {"success": False, "error": "Invalid steps"}
            return {"success": True, "steps": steps}
        return {"success": False, "error": "unknown"}

    port, stop, srv, th = start_mock_clo_server(handler)
    try:
        client = CLOClient(host="127.0.0.1", port=port, timeout=2)
        res = client.connect(retries=2)
        assert res["ok"] is True

        r1 = client.import_garment("C:/tmp/test.zprj")
        assert r1["ok"] is True
        assert r1["data"]["echo"]["path"].endswith("test.zprj")

        r2 = client.take_screenshot("C:/tmp/out.png", 640, 360)
        assert r2["ok"] is True
        assert r2["data"]["path"].endswith("out.png")

        r3 = client.run_simulation(steps=-5)
        assert r3["ok"] is False
        assert "Invalid steps" in r3["error"]
    finally:
        stop["flag"] = True
        try:
            srv.close()
        except Exception:
            pass
        # give thread time to stop
        time.sleep(0.2)


def test_timeout_and_broken_connection():
    def handler(req):
        # simulate no response for certain cmd
        if req.get("cmd") == "hang":
            time.sleep(3)
            return {"success": True}
        return {"success": True}

    port, stop, srv, th = start_mock_clo_server(handler)
    try:
        client = CLOClient(host="127.0.0.1", port=port, timeout=1)
        # This will timeout because server sleeps longer than timeout
        out = client.send({"cmd": "hang"})
        assert out["ok"] is False
        assert "timeout" in out["error"].lower()

        # Close server to simulate broken connection
        stop["flag"] = True
        srv.close()
        time.sleep(0.2)

        out2 = client.connect(retries=1)
        assert out2["ok"] is False
        assert any(k in out2 for k in ("error", "help"))
    finally:
        stop["flag"] = True
        try:
            srv.close()
        except Exception:
            pass
        time.sleep(0.2)


