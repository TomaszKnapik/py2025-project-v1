import csv
import json
import os
import zipfile
from datetime import datetime, timedelta
import io
import socket
import threading

class NetworkClient:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.lock = threading.Lock()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def send(self, data_dict):
        import json
        try:
            msg = json.dumps(data_dict) + "\n"
            with self.lock:
                self.sock.sendall(msg.encode())
        except Exception as e:
            print(f"[NetworkClient] Błąd wysyłki danych: {e}")

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

class Logger:
    def __init__(self, config_path: str, server_host: str, server_port: int):
        with open(config_path) as f:
            config = json.load(f)
        self.log_dir = config['log_dir']
        self.filename_pattern = config['filename_pattern']
        self.buffer_size = config['buffer_size']
        self.rotate_every_hours = config.get('rotate_every_hours', 24)
        self.max_size_mb = config.get('max_size_mb', 10)
        self.rotate_after_lines = config.get('rotate_after_lines')
        self.retention_days = config.get('retention_days', 30)

        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(os.path.join(self.log_dir, 'archive'), exist_ok=True)

        self.buffer = []
        self.current_file = None
        self.current_filename = None
        self.current_size = 0
        self.line_count = 0
        self.next_rotation_time = None

        # Sieć
        self.network_client = NetworkClient(server_host, server_port)
        self.network_client.connect()

    def start(self):
        self._rotate()

    def stop(self):
        self._flush_buffer()
        if self.current_file:
            self.current_file.close()
            self.current_file = None
            self.current_filename = None
        self.network_client.close()

    def log_reading(self, sensor_id: str, timestamp: datetime, value: float, unit: str):
        self.buffer.append((timestamp, sensor_id, value, unit))
        if len(self.buffer) >= self.buffer_size:
            self._flush_buffer()
        self._check_rotation()

    def log_and_send(self, sensor_id, timestamp, value, unit):
        self.log_reading(sensor_id, timestamp, value, unit)
        try:
            self.network_client.send({
                "timestamp": timestamp.isoformat(),
                "sensor_id": sensor_id,
                "value": value,
                "unit": unit
            })
        except Exception as e:
            print(f"[Logger] Błąd wysyłania danych do serwera: {e}")

    def _flush_buffer(self):
        if not self.current_file:
            self._open_file()
        writer = csv.writer(self.current_file)
        for entry in self.buffer:
            writer.writerow([entry[0].isoformat(), entry[1], entry[2], entry[3]])
            self.line_count += 1
            self.current_size += len(f"{entry[0]},{entry[1]},{entry[2]},{entry[3]}\n".encode())
        self.buffer.clear()
        self.current_file.flush()

    def _open_file(self):
        self.current_filename = datetime.now().strftime(self.filename_pattern)
        file_path = os.path.join(self.log_dir, self.current_filename)
        file_exists = os.path.exists(file_path)
        self.current_file = open(file_path, 'a', newline='')
        if not file_exists:
            writer = csv.writer(self.current_file)
            writer.writerow(['timestamp', 'sensor_id', 'value', 'unit'])
            self.current_size = os.path.getsize(file_path)
            self.line_count = 0
        else:
            self.current_size = os.path.getsize(file_path)
            with open(file_path, 'r') as f:
                self.line_count = sum(1 for _ in f) - 1
        self.next_rotation_time = datetime.now() + timedelta(hours=self.rotate_every_hours)

    def _check_rotation(self):
        now = datetime.now()
        if (now >= self.next_rotation_time or
                self.current_size >= self.max_size_mb * 1024 ** 2 or
                (self.rotate_after_lines and self.line_count >= self.rotate_after_lines)):
            self._rotate()

    def _rotate(self):
        self._flush_buffer()
        if self.current_file:
            self.current_file.close()
            self.current_file = None
        if self.current_filename:
            source = os.path.join(self.log_dir, self.current_filename)
            if os.path.exists(source):
                self._archive_file(source)
                self._clean_old_archives()
        self._open_file()

    def _archive_file(self, source):
        archive_path = os.path.join(self.log_dir, 'archive', os.path.basename(source) + '.zip')
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.write(source, os.path.basename(source))
        os.remove(source)

    def _clean_old_archives(self):
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        archive_dir = os.path.join(self.log_dir, 'archive')
        for filename in os.listdir(archive_dir):
            if filename.endswith('.zip'):
                path = os.path.join(archive_dir, filename)
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                if mtime < cutoff:
                    os.remove(path)
