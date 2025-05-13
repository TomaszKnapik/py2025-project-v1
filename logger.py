import csv
import json
import os
import zipfile
from datetime import datetime, timedelta
from typing import Optional, Dict, Iterator
import io


class Logger:
    def __init__(self, config_path: str):
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
        self.current_writer = None
        self.current_filename = None
        self.current_size = 0
        self.line_count = 0
        self.next_rotation_time = None

    def start(self):
        self._rotate()

    def stop(self):
        self._flush_buffer()
        if self.current_file:
            self.current_file.close()
            self.current_file = None
            self.current_writer = None
            self.current_filename = None

    def log_reading(self, sensor_id: str, timestamp: datetime, value: float, unit: str):
        self.buffer.append((timestamp, sensor_id, value, unit))
        if len(self.buffer) >= self.buffer_size:
            self._flush_buffer()
        self._check_rotation()

    def read_logs(self, start: datetime, end: datetime, sensor_id: Optional[str] = None) -> Iterator[Dict]:
        for dir_path in [self.log_dir, os.path.join(self.log_dir, 'archive')]:
            if not os.path.exists(dir_path):
                continue
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                if filename.endswith('.csv'):
                    yield from self._read_csv(file_path, start, end, sensor_id)
                elif filename.endswith('.zip'):
                    yield from self._read_zip(file_path, start, end, sensor_id)

    def _read_csv(self, file_path, start, end, sensor_id):
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                timestamp = datetime.fromisoformat(row[0])
                if start <= timestamp <= end and (sensor_id is None or row[1] == sensor_id):
                    yield {
                        "timestamp": timestamp,
                        "sensor_id": row[1],
                        "value": float(row[2]),
                        "unit": row[3]
                    }

    def _read_zip(self, file_path, start, end, sensor_id):
        with zipfile.ZipFile(file_path, 'r') as zf:
            for name in zf.namelist():
                if name.endswith('.csv'):
                    with zf.open(name) as f:
                        reader = csv.reader(io.TextIOWrapper(f))
                        next(reader)
                        for row in reader:
                            timestamp = datetime.fromisoformat(row[0])
                            if start <= timestamp <= end and (sensor_id is None or row[1] == sensor_id):
                                yield {
                                    "timestamp": timestamp,
                                    "sensor_id": row[1],
                                    "value": float(row[2]),
                                    "unit": row[3]
                                }

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
        self.stop()
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
        for filename in os.listdir(os.path.join(self.log_dir, 'archive')):
            if filename.endswith('.zip'):
                path = os.path.join(self.log_dir, 'archive', filename)
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                if mtime < cutoff:
                    os.remove(path)