#!/usr/bin/env python3

"""
Send one authenticated simulated PlantLife365 telemetry report.

Example:

python scripts/simulate_device.py \
    --device-id plantlife365-device-001 \
    --token YOUR_DEVICE_SECRET
"""

import argparse
import json
from pathlib import Path

import requests


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Send one authenticated simulated "
            "PlantLife365 telemetry report."
        )
    )

    parser.add_argument(
        "--server",
        default="http://127.0.0.1:8000",
        help="PlantLife365 server base URL",
    )

    parser.add_argument(
        "--device-id",
        required=True,
        help="Registered HardwareDevice.device_id",
    )

    parser.add_argument(
        "--token",
        required=True,
        help="Device authentication secret",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=24.5,
    )

    parser.add_argument(
        "--humidity",
        type=float,
        default=55.0,
    )

    parser.add_argument(
        "--light",
        type=float,
        default=70.0,
    )

    parser.add_argument(
        "--water-level",
        type=float,
        default=45.0,
    )

    parser.add_argument(
        "--gas",
        type=float,
        default=10.0,
    )

    parser.add_argument(
        "--image",
        type=Path,
        help="Optional JPEG image",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    payload = {
        "device_id": args.device_id,
        "temp": args.temperature,
        "humidity": args.humidity,
        "light": args.light,
        "water_level": args.water_level,
        "gas": args.gas,
    }

    headers = {
        "X-PlantLife365-Token": args.token,
    }

    image_handle = None
    files = None

    try:

        if args.image is not None:

            if not args.image.is_file():

                raise FileNotFoundError(
                    f"Image not found: {args.image}"
                )

            image_handle = args.image.open(
                "rb"
            )

            files = {
                "image": (
                    args.image.name,
                    image_handle,
                    "image/jpeg",
                )
            }

        response = requests.post(
            args.server.rstrip("/")
            + "/upload",
            headers=headers,
            data={
                "data": json.dumps(
                    payload
                )
            },
            files=files,
            timeout=15,
        )

        print(
            "HTTP status:",
            response.status_code,
        )

        try:

            print(
                json.dumps(
                    response.json(),
                    indent=2,
                )
            )

        except ValueError:

            print(
                response.text
            )

        response.raise_for_status()

    finally:

        if image_handle is not None:
            image_handle.close()


if __name__ == "__main__":
    main()
