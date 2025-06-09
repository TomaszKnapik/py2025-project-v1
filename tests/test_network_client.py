import socket
import threading
from network.client import NetworkClient


def echo_server(host, port):
    def handler(conn, _):
        data = conn.recv(1024)
        if data:
            conn.sendall(b"ACK\n")
        conn.close()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)
    threading.Thread(target=lambda: handler(*server.accept()), daemon=True).start()
    return server


def test_network_client_send():
    host, port = "127.0.0.1", 9001
    server = echo_server(host, port)

    client = NetworkClient(host, port)
    result = client.send({"sensor_id": "Test", "value": 42})
    client.close()

    assert result is True
    server.close()
