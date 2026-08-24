"""
Data-access and aggregation services for PlantLife365.

This module centralizes user-scoped telemetry queries so dashboard,
history, statistics, exports, and future analytics operate on the same
data boundary.
"""

import math
from datetime import timedelta

from django.db.models import Avg, Max, Min
from django.utils import timezone

from .models import HardwareDevice, SensorReading


HISTORY_PERIODS = {
    "1h": timedelta(hours=1),
    "1d": timedelta(days=1),
    "1w": timedelta(weeks=1),
}


def get_user_device_ids(
    user,
    active_only=True,
):
    """
    Return device IDs belonging to one authenticated user.
    """

    devices = HardwareDevice.objects.filter(
        owner=user
    )

    if active_only:
        devices = devices.filter(
            is_active=True
        )

    return devices.values_list(
        "device_id",
        flat=True,
    )


def get_latest_reading(user):
    """
    Return the newest reading across the user's active devices.
    """

    device_ids = get_user_device_ids(
        user,
        active_only=True,
    )

    if not device_ids.exists():
        return None

    return (
        SensorReading.objects
        .filter(
            device_id__in=device_ids
        )
        .order_by(
            "-timestamp"
        )
        .first()
    )


def get_history(
    user,
    period,
    max_points=100,
):
    """
    Return time-ordered telemetry for a supported historical period.

    Large result sets are uniformly downsampled to keep dashboard
    responses bounded.
    """

    if period not in HISTORY_PERIODS:
        return []

    device_ids = get_user_device_ids(
        user,
        active_only=True,
    )

    if not device_ids.exists():
        return []

    start_time = (
        timezone.now()
        - HISTORY_PERIODS[period]
    )

    queryset = (
        SensorReading.objects
        .filter(
            device_id__in=device_ids,
            timestamp__gte=start_time,
        )
        .order_by(
            "timestamp"
        )
    )

    rows = list(
        queryset
    )

    if not rows:
        return []

    if len(rows) <= max_points:
        return rows

    step = max(
        1,
        math.ceil(
            len(rows)
            / max_points
        ),
    )

    sampled = rows[::step]

    if sampled[-1].id != rows[-1].id:
        sampled.append(
            rows[-1]
        )

    return sampled


def get_daily_statistics(
    user,
    hours=24,
):
    """
    Aggregate min, average, and max values across the user's active
    devices over a rolling time window.
    """

    device_ids = get_user_device_ids(
        user,
        active_only=True,
    )

    if not device_ids.exists():
        return None

    start_time = (
        timezone.now()
        - timedelta(
            hours=hours
        )
    )

    readings = SensorReading.objects.filter(
        device_id__in=device_ids,
        timestamp__gte=start_time,
    )

    if not readings.exists():
        return None

    stats = readings.aggregate(
        temp_min=Min("temperature"),
        temp_max=Max("temperature"),
        temp_avg=Avg("temperature"),

        humid_min=Min("humidity"),
        humid_max=Max("humidity"),
        humid_avg=Avg("humidity"),

        water_min=Min("water_level"),
        water_max=Max("water_level"),
        water_avg=Avg("water_level"),

        light_min=Min("light"),
        light_max=Max("light"),
        light_avg=Avg("light"),

        gas_min=Min("gas"),
        gas_max=Max("gas"),
        gas_avg=Avg("gas"),
    )

    stats["reading_count"] = readings.count()

    return stats


def get_readings_for_date(
    user,
    date_value,
):
    """
    Return all readings belonging to the user's active devices on one
    calendar date.
    """

    device_ids = get_user_device_ids(
        user,
        active_only=True,
    )

    if not device_ids.exists():
        return SensorReading.objects.none()

    return (
        SensorReading.objects
        .filter(
            device_id__in=device_ids,
            timestamp__date=date_value,
        )
        .order_by(
            "timestamp"
        )
    )
