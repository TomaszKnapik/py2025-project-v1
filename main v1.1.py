import math
import random
import time
from datetime import datetime


class TemperatureSensor:
    monthly_avg = {
        1: -3.6, 2: -1.7, 3: 3.3, 4: 8.8, 5: 13.5, 6: 16.4,
        7: 17.9, 8: 17.5, 9: 14.1, 10: 9.4, 11: 3.7, 12: -1.2
    }

    def get_reading(self, date, hour):
        month = date.month
        base_temp = self.monthly_avg[month]
        phase = (hour - 15) * (2 * math.pi / 24)
        variation = 6 * math.cos(phase)
        temp = base_temp + variation
        return round(max(-12, min(32, temp)), 1)


class PressureSensor:
    def get_reading(self):
        pressure = random.gauss(1017.8, 10)
        return round(max(986.8, min(1041.6, pressure)), 1)


class LightSensor:
    def get_reading(self, hour):
        if 6 <= hour < 18:
            return round(random.uniform(10000, 25000), 1) if random.random() < 0.7 else 107.0
        elif 4 <= hour < 6 or 18 <= hour < 20:
            return round(random.uniform(1.8, 10.8), 1)
        else:
            choices = {'pochmurna': 0.0001, 'rozgwiezdzone': 0.0011, 'księżyc': 0.108,
                       'uliczne': round(random.uniform(5, 10), 1)}
            return choices[random.choices(list(choices.keys()), weights=[0.3, 0.3, 0.2, 0.2])[0]]


class AirQualitySensor:
    def get_reading(self):
        aq = random.gauss(15.2, 3)
        return round(max(11.1, min(29.9, aq)), 1)


# Pobieranie daty i godziny
def get_current_datetime():
    return datetime.now()


# Pobieranie wyników w pętli
def run_sensor_readings(interval=5):
    sensors = [
        ("TemperatureSensor", TemperatureSensor()),
        ("PressureSensor", PressureSensor()),
        ("LightSensor", LightSensor()),
        ("AirQualitySensor", AirQualitySensor())
    ]

    while True:
        now = get_current_datetime()
        date, hour = now.date(), now.hour

        print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}]")
        for name, sensor in sensors:
            if name == "TemperatureSensor":
                value = sensor.get_reading(date, hour)
            elif name == "LightSensor":
                value = sensor.get_reading(hour)
            else:
                value = sensor.get_reading()
            print(f"{name}: {value}")

        time.sleep(interval)


# Uruchomienie
run_sensor_readings()
