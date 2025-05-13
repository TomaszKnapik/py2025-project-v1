from datetime import datetime
import time
from sensors import TemperatureSensor, PressureSensor, LightSensor, AirQualitySensor
from logger import Logger


def run_sensor_readings(interval=5):
    sensors = [
        ("TemperatureSensor", TemperatureSensor()),
        ("PressureSensor", PressureSensor()),
        ("LightSensor", LightSensor()),
        ("AirQualitySensor", AirQualitySensor())
    ]

    logger = Logger("config.json")
    logger.start()

    for name, sensor in sensors:
        sensor.register_callback(logger.log_reading)

    try:
        while True:
            now = datetime.now()
            date, hour = now.date(), now.hour

            print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}]")
            for name, sensor in sensors:
                if name == "TemperatureSensor":
                    value = sensor.get_reading(now)
                elif name == "LightSensor":
                    value = sensor.get_reading(hour)
                else:
                    value = sensor.get_reading()
                print(f"{name}: {value}")

            time.sleep(interval)
    except KeyboardInterrupt:
        logger.stop()
        print("\nZamykanie systemu...")


if __name__ == "__main__":
    run_sensor_readings()