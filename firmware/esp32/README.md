# ESP32 Firmware

This directory contains the maintained ESP32/MicroPython telemetry
firmware recovered from the historical PlantLife365 development
archive.

## Configuration

Copy:

`config.example.py`

to:

`config.py`

and provide deployment-specific values for:

- `WIFI_SSID`
- `WIFI_PASS`
- `PC_IP`
- `PC_PORT`
- `DEVICE_ID`
- `DEVICE_TOKEN`

The real `config.py` is excluded from Git.

## Device authentication

`DEVICE_ID` identifies the registered PlantLife365 hardware device.

`DEVICE_TOKEN` must match the Device Password / Secret PIN associated
with the same `HardwareDevice` in Django.

The firmware sends the token through:

`X-PlantLife365-Token`

The Django application stores the corresponding secret using Django
password hashing.

## Telemetry

The maintained firmware sends:

- temperature
- humidity
- light percentage
- water-level percentage
- gas percentage
- optional JPEG camera image

to:

`POST /upload`

## Security scope

The current implementation uses a per-device shared secret.

This prevents telemetry submission using only knowledge of a valid
device identifier.

Additional production hardening may include:

- HTTPS/TLS
- token rotation
- replay protection
- rate limiting
- device certificates
- secure centralized provisioning
