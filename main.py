import time
from datetime import datetime
from logger import Logger
from sensors import TemperatureSensor, PressureSensor, LightSensor, AirQualitySensor

CONFIG_PATH = "logger_config.json"
SERVER_HOST = "localhost"
SERVER_PORT = 9000

logger = Logger(CONFIG_PATH, SERVER_HOST, SERVER_PORT)
logger.start()

temperature_sensor = TemperatureSensor()
pressure_sensor = PressureSensor()
light_sensor = LightSensor()
air_quality_sensor = AirQualitySensor()

for sensor in [temperature_sensor, pressure_sensor, light_sensor, air_quality_sensor]:
    sensor.register_callback(logger.log_and_send)

try:
    while True:
        now = datetime.now()
        temperature_sensor.get_reading(now)
        pressure_sensor.get_reading()
        light_sensor.get_reading(now.hour)
        air_quality_sensor.get_reading()

        time.sleep(10)

except KeyboardInterrupt:
    print("Zatrzymywanie programu...")
    logger.stop()
