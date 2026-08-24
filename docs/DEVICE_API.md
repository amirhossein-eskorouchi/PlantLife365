# Device Telemetry API

## Endpoint

The canonical PlantLife365 telemetry endpoint is:

`POST /upload`

The request uses `multipart/form-data`.

## Authentication

Each telemetry request must include the HTTP header:

`X-PlantLife365-Token`

The submitted secret must correspond to the `device_id` contained in
the telemetry payload.

The server validates the secret against the stored `HardwareDevice`
password hash.

Knowledge of a valid device identifier alone is therefore insufficient
to submit telemetry.

## Data field

The multipart field `data` contains JSON with:

- `device_id`
- `temp`
- `humidity`
- `light`
- `water_level`
- `gas`

Example payload:

    {
      "device_id": "plantlife365-device-001",
      "temp": 24.5,
      "humidity": 55.0,
      "light": 70.0,
      "water_level": 45.0,
      "gas": 10.0
    }

## Application-level validation ranges

Temperature:

- minimum: -40
- maximum: 100

Humidity:

- minimum: 0
- maximum: 100

Light:

- minimum: 0
- maximum: 100

Water level:

- minimum: 0
- maximum: 100

Gas:

- minimum: 0
- maximum: 100

These are ingestion-validation bounds rather than sensor-calibration
claims.

## Optional image

The multipart field `image` may contain a JPEG image.

The default maximum accepted size is 2,000,000 bytes.

The limit can be configured through:

`PLANTLIFE365_MAX_IMAGE_BYTES`

The application verifies the actual JPEG structure using Pillow.

## Responses

Successful ingestion:

`201 Created`

Malformed telemetry:

`400 Bad Request`

Unknown, inactive, or incorrectly authenticated device:

`403 Forbidden`

Unexpected processing failure:

`500 Internal Server Error`

## Device provisioning

For the current research/development workflow:

1. Create or pair a device through PlantLife365.
2. Assign the device ID and Device Password / Secret PIN.
3. Set the same ID as `DEVICE_ID` in ESP32 `config.py`.
4. Set the same secret as `DEVICE_TOKEN`.
5. Never commit the real `config.py`.

## Simulator

Use:

`python scripts/simulate_device.py --device-id plantlife365-device-001 --token YOUR_DEVICE_SECRET`

An optional JPEG may be supplied with:

`--image path/to/example.jpg`

## Production limitation

The current research implementation uses per-device shared-secret
authentication.

An internet-facing production deployment should additionally consider:

- TLS
- replay protection
- token rotation
- request throttling
- certificate-based device identity
- secure secret provisioning
