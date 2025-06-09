import os
import shutil
import tempfile
from datetime import datetime, timedelta
from logger import Logger

def test_logger_write_and_read():
    temp_dir = tempfile.mkdtemp()
    config = {
        "log_dir": temp_dir,
        "filename_pattern": "test_%Y%m%d_%H%M.csv",
        "buffer_size": 1,
        "rotate_every_hours": 1,
        "max_size_mb": 1,
        "retention_days": 1
    }
    config_path = os.path.join(temp_dir, "config.json")
    with open(config_path, "w") as f:
        import json
        json.dump(config, f)

    logger = Logger(config_path)
    logger.start()

    now = datetime.now()
    logger.log_reading("TestSensor", now, 12.3, "unit")
    logger.stop()

    logs = list(logger.read_logs(now - timedelta(minutes=1), now + timedelta(minutes=1)))
    assert len(logs) == 1
    assert logs[0]["sensor_id"] == "TestSensor"
    assert logs[0]["value"] == 12.3

    shutil.rmtree(temp_dir)
