from PyQt6.QtWidgets import (
    QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem, QStatusBar, QApplication, QMessageBox
)
from PyQt6.QtCore import QTimer
from datetime import datetime, timedelta
from collections import defaultdict, deque

from server.server import NetworkServer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Serwer Sensorów")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)

        top_layout.addWidget(QLabel("Port TCP:"))
        self.port_input = QLineEdit("9000")
        self.port_input.setFixedWidth(80)
        top_layout.addWidget(self.port_input)

        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        top_layout.addWidget(self.start_button)
        top_layout.addWidget(self.stop_button)

        self.sensor_table = QTableWidget(0, 6)
        self.sensor_table.setHorizontalHeaderLabels([
            "Sensor", "Ostatnia wartość", "Jednostka", "Timestamp", "Średnia 1h", "Średnia 12h"
        ])
        self.sensor_table.verticalHeader().setVisible(False)
        self.sensor_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sensor_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.sensor_table)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.sensor_data = defaultdict(lambda: deque())

        self.server = None

        self.update_timer = QTimer()
        self.update_timer.setInterval(3000)
        self.update_timer.timeout.connect(self.update_sensor_table)

        self.start_button.clicked.connect(self.start_server)
        self.stop_button.clicked.connect(self.stop_server)

    def start_server(self):
        port_text = self.port_input.text()
        try:
            port = int(port_text)
            if not (1 <= port <= 65535):
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Błąd", "Nieprawidłowy numer portu.")
            return

        try:
            self.server = NetworkServer(port=port)
            self.server.new_data.connect(self.handle_new_sensor_data)
            self.server.status_update.connect(self.handle_status_update)
            self.server.start()
        except Exception as e:
            QMessageBox.critical(self, "Błąd serwera", f"Nie udało się uruchomić serwera:\n{e}")
            return

        self.status_bar.showMessage(f"Serwer uruchomiony na porcie {port}")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.port_input.setEnabled(False)

        self.update_timer.start()

    def stop_server(self):
        if self.server:
            self.server.stop()
            self.server = None

        self.status_bar.showMessage("Serwer zatrzymany")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.port_input.setEnabled(True)

        self.update_timer.stop()

    def handle_new_sensor_data(self, data: dict):
        sensor_id = data.get("sensor_id") or data.get("Sensor") or "UNKNOWN"
        value = data.get("value")
        unit = data.get("unit")
        timestamp_str = data.get("timestamp")
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except Exception:
            timestamp = datetime.now()

        buffer = self.sensor_data[sensor_id]

        # Usuwamy odczyty starsze niż 12h
        cutoff = datetime.now() - timedelta(hours=12)
        while buffer and buffer[0][0] < cutoff:
            buffer.popleft()

        buffer.append((timestamp, value, unit))

    def handle_status_update(self, message: str):
        self.status_bar.showMessage(message)

    def update_sensor_table(self):
        sensors = list(self.sensor_data.keys())
        self.sensor_table.setRowCount(len(sensors))

        now = datetime.now()
        for row, sensor_id in enumerate(sensors):
            readings = self.sensor_data[sensor_id]
            if not readings:
                continue

            last_ts, last_val, last_unit = readings[-1]

            cutoff_1h = now - timedelta(hours=1)
            values_1h = [v for (ts, v, u) in readings if ts >= cutoff_1h]
            avg_1h = round(sum(values_1h) / len(values_1h), 2) if values_1h else None

            values_12h = [v for (ts, v, u) in readings]
            avg_12h = round(sum(values_12h) / len(values_12h), 2) if values_12h else None

            self.sensor_table.setItem(row, 0, QTableWidgetItem(str(sensor_id)))
            self.sensor_table.setItem(row, 1, QTableWidgetItem(str(last_val)))
            self.sensor_table.setItem(row, 2, QTableWidgetItem(str(last_unit)))
            self.sensor_table.setItem(row, 3, QTableWidgetItem(last_ts.strftime("%Y-%m-%d %H:%M:%S")))
            self.sensor_table.setItem(row, 4, QTableWidgetItem(str(avg_1h) if avg_1h is not None else ""))
            self.sensor_table.setItem(row, 5, QTableWidgetItem(str(avg_12h) if avg_12h is not None else ""))

        self.sensor_table.resizeColumnsToContents()
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
