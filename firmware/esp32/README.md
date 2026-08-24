# ESP32 Firmware

This directory contains the initial maintained ESP32/MicroPython
firmware candidate recovered from the historical PlantLife365
development archive.

## Configuration

Device-specific values are intentionally excluded from Git.

1. Copy:

   `config.example.py` → `config.py`

2. Set the device-specific:

   - access-point SSID
   - access-point password
   - server IP
   - server port
   - device identifier

3. Deploy `main.py` and `config.py` to the ESP32.

`config.py` is ignored by Git.

## Current telemetry

The recovered canonical firmware collects:

- temperature
- humidity
- light
- water level
- gas measurement
- JPEG camera image

and sends them to the Django `/upload` endpoint.

## Security status

Batch 2 externalizes deployment credentials.

Per-device authenticated telemetry is intentionally deferred to
Batch 3 and must be completed before the ingestion interface is
considered hardened.
