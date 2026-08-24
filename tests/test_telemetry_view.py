import json

from django.test import RequestFactory

from dashboard.models import SensorReading
from dashboard.views import receive_esp32_data


def telemetry_payload(device_id):
    return {
        "device_id": device_id,
        "temp": 24.0,
        "humidity": 50.0,
        "light": 75.0,
        "water_level": 40.0,
        "gas": 10.0,
    }


def test_telemetry_without_token_is_rejected(
    db,
    device,
):
    factory = RequestFactory()

    request = factory.post(
        "/upload",
        data={
            "data": json.dumps(
                telemetry_payload(
                    device.device_id
                )
            )
        },
    )

    response = receive_esp32_data(
        request
    )

    assert response.status_code == 403

    assert SensorReading.objects.count() == 0


def test_telemetry_with_wrong_token_is_rejected(
    db,
    device,
):
    factory = RequestFactory()

    request = factory.post(
        "/upload",
        data={
            "data": json.dumps(
                telemetry_payload(
                    device.device_id
                )
            )
        },
        HTTP_X_PLANTLIFE365_TOKEN="wrong-secret",
    )

    response = receive_esp32_data(
        request
    )

    assert response.status_code == 403

    assert SensorReading.objects.count() == 0


def test_authenticated_telemetry_is_stored(
    db,
    device,
):
    factory = RequestFactory()

    request = factory.post(
        "/upload",
        data={
            "data": json.dumps(
                telemetry_payload(
                    device.device_id
                )
            )
        },
        HTTP_X_PLANTLIFE365_TOKEN="device-secret-001",
    )

    response = receive_esp32_data(
        request
    )

    assert response.status_code == 201

    assert SensorReading.objects.count() == 1

    reading = SensorReading.objects.get()

    assert reading.device_id == device.device_id
    assert reading.temperature == 24.0
    assert reading.humidity == 50.0
