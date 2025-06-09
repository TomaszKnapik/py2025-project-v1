import socket
import threading
import json
from server.server import NetworkServer


def test_server_receives_ack(monkeypatch):
    responses = []

    def run_server():
        server = NetworkServer(port=9002)
        threading.Thread(target=server.start, daemon=True).start()

    run_server()

    def client_send():
        with socket.create_connection(("127.0.0.1", 9002), timeout=5) as sock:
            data = json.dumps({"sensor_id": "Light", "value": 77}).encode()
            sock.sendall(data + b"\n")
            ack = sock.recv(1024)
            responses.append(ack.strip())

    import time
    time.sleep(1)  # Give server time to start
    client_send()

    assert responses[0] == b"ACK"
