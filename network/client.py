import socket
import json
import logging
import time
from typing import Optional

class NetworkClient:
    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 5.0,
        retries: int = 3,
        logger: Optional[logging.Logger] = None
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self.sock: Optional[socket.socket] = None
        self.logger = logger or logging.getLogger(__name__)
        self.connected = False

    def connect(self) -> None:
        if self.connected:
            self.logger.info("Already connected")
            return
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.port))
            self.connected = True
            self.logger.info(f"Connected to {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.host}:{self.port}: {e}")
            self.connected = False
            if self.sock:
                self.sock.close()
                self.sock = None
            raise

    def send(self, data: dict) -> bool:
        if not self.connected:
            try:
                self.connect()
            except Exception:
                return False

        serialized = self._serialize(data)
        attempts = 0

        while attempts < self.retries:
            try:
                self.sock.sendall(serialized + b"\n")
                self.logger.info(f"Sent data: {data}")
                ack = self._recv_ack()
                if ack == "ACK":
                    self.logger.info("Received ACK")
                    return True
                else:
                    self.logger.error(f"Unexpected response instead of ACK: {ack}")
            except Exception as e:
                self.logger.error(f"Send error (attempt {attempts+1}): {e}")
                # reconnect on error
                self._reconnect()
            attempts += 1
            time.sleep(1)  # small delay before retry
        self.logger.error("Failed to send data after retries")
        return False

    def close(self) -> None:
        if self.sock:
            try:
                self.sock.close()
                self.logger.info("Socket closed")
            except Exception as e:
                self.logger.error(f"Error closing socket: {e}")
            finally:
                self.sock = None
                self.connected = False

    def _serialize(self, data: dict) -> bytes:
        try:
            return json.dumps(data).encode("utf-8")
        except Exception as e:
            self.logger.error(f"Serialization error: {e}")
            raise

    def _deserialize(self, raw: bytes) -> dict:
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception as e:
            self.logger.error(f"Deserialization error: {e}")
            raise

    def _recv_ack(self) -> str:

        if not self.sock:
            raise ConnectionError("Socket is not connected")
        chunks = []
        while True:
            chunk = self.sock.recv(1)
            if not chunk:
                break
            if chunk == b"\n":
                break
            chunks.append(chunk)
        return b"".join(chunks).decode("utf-8")

    def _reconnect(self) -> None:
        self.close()
        try:
            self.connect()
        except Exception as e:
            self.logger.error(f"Reconnect failed: {e}")
