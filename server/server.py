import socket
import threading
import json
import logging
import time

from PyQt6.QtCore import QObject, pyqtSignal


class NetworkServer(QObject):
    new_data = pyqtSignal(dict)
    status_update = pyqtSignal(str)

    def __init__(self, port: int, logger: logging.Logger = None):
        super().__init__()
        self.port = port
        self.logger = logger or logging.getLogger(__name__)
        self._sock = None
        self._running = False
        self._thread = None

    def start(self) -> None:
        if self._running:
            self.logger.info("Server is already running")
            return

        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind(('', self.port))
            self._sock.listen()
            self._running = True
            self.logger.info(f"Server listening on port {self.port}")
            self.status_update.emit(f"Serwer nasłuchuje na porcie {self.port}")

            self._thread = threading.Thread(target=self._accept_clients, daemon=True)
            self._thread.start()
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            self.status_update.emit(f"Błąd uruchamiania serwera: {e}")
            self._running = False
            if self._sock:
                self._sock.close()
                self._sock = None
            raise

    def stop(self) -> None:
        self._running = False
        if self._sock:
            try:
                self._sock.close()
                self.logger.info("Server socket closed")
            except Exception as e:
                self.logger.error(f"Error closing server socket: {e}")
            finally:
                self._sock = None

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
            self.logger.info("Server thread stopped")

        self.status_update.emit("Serwer zatrzymany")

    def _accept_clients(self) -> None:
        while self._running:
            try:
                client_sock, addr = self._sock.accept()
                self.logger.info(f"Connection from {addr}")
                self.status_update.emit(f"Połączono z {addr}")
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, addr),
                    daemon=True
                )
                client_thread.start()
            except OSError:
                break
            except Exception as e:
                self.logger.error(f"Error accepting client: {e}")
                self.status_update.emit(f"Błąd połączenia klienta: {e}")

    def _handle_client(self, client_socket: socket.socket, addr) -> None:
        try:
            with client_socket:
                buffer = b""
                while self._running:
                    chunk = client_socket.recv(1024)
                    if not chunk:
                        break
                    buffer += chunk

                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        try:
                            message = json.loads(line.decode('utf-8'))
                            self.logger.info(f"Received from {addr}: {message}")
                            self.new_data.emit(message)
                            client_socket.sendall(b"ACK\n")
                        except json.JSONDecodeError as e:
                            self.logger.error(f"JSON error from {addr}: {e}")
                            self.status_update.emit(f"Błąd dekodowania JSON od {addr}")
        except Exception as e:
            self.logger.error(f"Error handling client {addr}: {e}")
            self.status_update.emit(f"Błąd obsługi klienta {addr}: {e}")
