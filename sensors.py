import math
import random
from datetime import datetime, time

class Sensor:
    def __init__(self):
        self.callbacks = []

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def _notify_callbacks(self, timestamp, value, unit):
        for callback in self.callbacks:
            callback(self.__class__.__name__, timestamp, value, unit)


class TemperatureSensor(Sensor):
    monthly_avg = {
        1: -3.6, 2: -1.7, 3: 3.3, 4: 8.8, 5: 13.5, 6: 16.4,
        7: 17.9, 8: 17.5, 9: 14.1, 10: 9.4, 11: 3.7, 12: -1.2
    }

    def get_reading(self, current_datetime):
        month = current_datetime.month
        hour = current_datetime.hour
        base_temp = self.monthly_avg[month]
        phase = (hour - 15) * (2 * math.pi / 24)
        variation = 6 * math.cos(phase)
        temp = base_temp + variation
        value = round(max(-12, min(32, temp)), 1)
        self._notify_callbacks(current_datetime, value, "°C")
        return value


class PressureSensor(Sensor):
    def get_reading(self):
        pressure = random.gauss(1017.8, 10)
        value = round(max(986.8, min(1041.6, pressure)), 1)
        self._notify_callbacks(datetime.now(), value, "hPa")
        return value


class LightSensor(Sensor):
    def get_reading(self, hour):
        if 6 <= hour < 18:
            value = round(random.uniform(10000, 25000), 1) if random.random() < 0.7 else 107.0
        elif 4 <= hour < 6 or 18 <= hour < 20:
            value = round(random.uniform(1.8, 10.8), 1)
        else:
            choices = {'pochmurna': 0.0001, 'rozgwiezdzone': 0.0011, 'księżyc': 0.108,
                       'uliczne': round(random.uniform(5, 10), 1)}
            value = choices[random.choices(list(choices.keys()), weights=[0.3, 0.3, 0.2, 0.2])[0]]
        self._notify_callbacks(datetime.now(), value, "lux")
        return value


class AirQualitySensor(Sensor):
    def get_reading(self):
        aq = random.gauss(15.2, 3)
        value = round(max(11.1, min(29.9, aq)), 1)
        self._notify_callbacks(datetime.now(), value, "AQI")
        return value