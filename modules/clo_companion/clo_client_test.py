import socket
import json
import sys

HOST = "127.0.0.1"
PORT = 51235

def main() -> int:
    try:
        with socket.create_connection((HOST, PORT), timeout=1.0) as s:
            s.sendall((json.dumps({"cmd": "get_garment_info"}) + "\n").encode("utf-8"))
            s.shutdown(socket.SHUT_WR)
            data = s.recv(8192)
        if not data:
            print("No response from CLO listener")
            return 1
        text = data.decode("utf-8", "ignore").strip()
        try:
            print(json.dumps(json.loads(text), indent=2))
        except Exception:
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    print(json.dumps(json.loads(line), indent=2))
                    return 0
                except Exception:
                    continue
            print(text)
        return 0
    except Exception:
        print("CLO listener not available")
        return 2

if __name__ == "__main__":
    sys.exit(main())


