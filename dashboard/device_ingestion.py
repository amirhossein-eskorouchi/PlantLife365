"""
Validation utilities for PlantLife365 device telemetry.

The historical application accepted data from a known active device ID
without authenticating the physical sender. The maintained application
requires a per-device shared secret and validates incoming telemetry.
"""

import json
import math
import os
import re

from PIL import Image, UnidentifiedImageError


DEVICE_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,99}$"
)

SENSOR_LIMITS = {
    "temp": (-40.0, 100.0),
    "humidity": (0.0, 100.0),
    "light": (0.0, 100.0),
    "water_level": (0.0, 100.0),
    "gas": (0.0, 100.0),
}

DEFAULT_MAX_IMAGE_BYTES = 2_000_000

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
}


class DevicePayloadError(ValueError):
    """Raised when incoming device telemetry fails validation."""


def _parse_number(name, value):
    if value is None:
        raise DevicePayloadError(
            f"Missing sensor field: {name}"
        )

    if isinstance(value, bool):
        raise DevicePayloadError(
            f"Invalid numeric value for {name}"
        )

    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise DevicePayloadError(
            f"Invalid numeric value for {name}"
        ) from exc

    if not math.isfinite(number):
        raise DevicePayloadError(
            f"Non-finite numeric value for {name}"
        )

    lower, upper = SENSOR_LIMITS[name]

    if number < lower or number > upper:
        raise DevicePayloadError(
            f"{name} outside accepted range "
            f"[{lower}, {upper}]"
        )

    return number


def parse_sensor_payload(raw_json):
    """
    Parse and validate JSON from the multipart ``data`` field.
    """

    if not raw_json:
        raise DevicePayloadError(
            "Missing multipart data field"
        )

    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise DevicePayloadError(
            "Malformed JSON payload"
        ) from exc

    if not isinstance(payload, dict):
        raise DevicePayloadError(
            "Telemetry payload must be a JSON object"
        )

    device_id = str(
        payload.get("device_id", "")
    ).strip()

    if not device_id:
        raise DevicePayloadError(
            "Missing device_id"
        )

    if not DEVICE_ID_PATTERN.fullmatch(device_id):
        raise DevicePayloadError(
            "Invalid device_id format"
        )

    clean_payload = {
        "device_id": device_id,
        "temp": _parse_number(
            "temp",
            payload.get("temp"),
        ),
        "humidity": _parse_number(
            "humidity",
            payload.get("humidity"),
        ),
        "light": _parse_number(
            "light",
            payload.get("light"),
        ),
        "water_level": _parse_number(
            "water_level",
            payload.get("water_level"),
        ),
        "gas": _parse_number(
            "gas",
            payload.get("gas"),
        ),
    }

    return clean_payload


def validate_image_upload(upload):
    """
    Validate an optional device JPEG upload.
    """

    if upload is None:
        return

    try:
        max_bytes = int(
            os.environ.get(
                "PLANTLIFE365_MAX_IMAGE_BYTES",
                str(DEFAULT_MAX_IMAGE_BYTES),
            )
        )
    except ValueError:
        max_bytes = DEFAULT_MAX_IMAGE_BYTES

    size = getattr(
        upload,
        "size",
        None,
    )

    if size is not None:
        if size > max_bytes:
            raise DevicePayloadError(
                f"Image exceeds maximum size of "
                f"{max_bytes} bytes"
            )

    content_type = (
        getattr(
            upload,
            "content_type",
            "",
        )
        or ""
    ).lower()

    if content_type:
        if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise DevicePayloadError(
                "Only JPEG device images are accepted"
            )

    try:
        upload.seek(0)

        with Image.open(upload) as image:
            image.verify()

            if image.format != "JPEG":
                raise DevicePayloadError(
                    "Uploaded image is not a valid JPEG"
                )

    except (UnidentifiedImageError, OSError) as exc:
        raise DevicePayloadError(
            "Uploaded image is not a valid JPEG"
        ) from exc

    finally:
        try:
            upload.seek(0)
        except Exception:
            pass
