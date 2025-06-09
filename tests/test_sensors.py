from sensors import TemperatureSensor
from datetime import datetime


def test_temperature_sensor_callback_called(mocker):
    sensor = TemperatureSensor()
    mock_callback = mocker.Mock()
    sensor.register_callback(mock_callback)

    dt = datetime(2023, 5, 1, 15, 0)
    result = sensor.get_reading(dt)

    mock_callback.assert_called_once()
    called_args = mock_callback.call_args[0]
    assert called_args[0] == "TemperatureSensor"
    assert isinstance(called_args[1], datetime)
    assert isinstance(called_args[2], float)
    assert called_args[3] == "°C"
