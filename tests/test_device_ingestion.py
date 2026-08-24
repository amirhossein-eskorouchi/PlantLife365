import json

import pytest

from dashboard.device_ingestion import (
    DevicePayloadError,
    parse_sensor_payload,
)


def valid_payload():
    return {
        "device_id": "plantlife365-device-001",
        "temp": 24.5,
        "humidity": 55.2,
        "light": 71.4,
        "water_level": 48.1,
        "gas": 9.3,
    }


def test_valid_sensor_payload_is_parsed():
    payload = parse_sensor_payload(
        json.dumps(
            valid_payload()
        )
    )

    assert payload["device_id"] == "plantlife365-device-001"
    assert payload["temp"] == 24.5
    assert payload["humidity"] == 55.2
    assert payload["light"] == 71.4
    assert payload["water_level"] == 48.1
    assert payload["gas"] == 9.3


def test_missing_json_is_rejected():
    with pytest.raises(
        DevicePayloadError
    ):
        parse_sensor_payload(
            None
        )


def test_malformed_json_is_rejected():
    with pytest.raises(
        DevicePayloadError
    ):
        parse_sensor_payload(
            "{not-valid-json"
        )


def test_missing_device_id_is_rejected():
    payload = valid_payload()

    payload.pop(
        "device_id"
    )

    with pytest.raises(
        DevicePayloadError
    ):
        parse_sensor_payload(
            json.dumps(
                payload
            )
        )


def test_invalid_device_id_is_rejected():
    payload = valid_payload()

    payload["device_id"] = "../unsafe"

    with pytest.raises(
        DevicePayloadError
    ):
        parse_sensor_payload(
            json.dumps(
                payload
            )
        )


def test_humidity_above_range_is_rejected():
    payload = valid_payload()

    payload["humidity"] = 101

    with pytest.raises(
        DevicePayloadError
    ):
        parse_sensor_payload(
            json.dumps(
                payload
            )
        )


def test_non_numeric_sensor_is_rejected():
    payload = valid_payload()

    payload["gas"] = "not-a-number"

    with pytest.raises(
        DevicePayloadError
    ):
        parse_sensor_payload(
            json.dumps(
                payload
            )
        )
