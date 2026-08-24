from django.utils import timezone

from dashboard.data_services import (
    get_daily_statistics,
    get_latest_reading,
    get_readings_for_date,
)
from dashboard.models import SensorReading


def test_latest_reading_is_user_scoped(
    user,
    device,
    second_device,
):
    own_reading = SensorReading.objects.create(
        temperature=21.0,
        humidity=50.0,
        light=60.0,
        water_level=40.0,
        gas=5.0,
        device_id=device.device_id,
    )

    SensorReading.objects.create(
        temperature=99.0,
        humidity=99.0,
        light=99.0,
        water_level=99.0,
        gas=99.0,
        device_id=second_device.device_id,
    )

    latest = get_latest_reading(
        user
    )

    assert latest is not None
    assert latest.id == own_reading.id
    assert latest.device_id == device.device_id


def test_daily_statistics_are_user_scoped(
    user,
    device,
    second_device,
):
    SensorReading.objects.create(
        temperature=20.0,
        humidity=40.0,
        light=60.0,
        water_level=30.0,
        gas=10.0,
        device_id=device.device_id,
    )

    SensorReading.objects.create(
        temperature=30.0,
        humidity=60.0,
        light=80.0,
        water_level=50.0,
        gas=20.0,
        device_id=device.device_id,
    )

    SensorReading.objects.create(
        temperature=100.0,
        humidity=100.0,
        light=100.0,
        water_level=100.0,
        gas=100.0,
        device_id=second_device.device_id,
    )

    stats = get_daily_statistics(
        user,
        hours=24,
    )

    assert stats is not None

    assert stats["reading_count"] == 2

    assert stats["temp_min"] == 20.0
    assert stats["temp_max"] == 30.0
    assert stats["temp_avg"] == 25.0


def test_date_query_is_user_scoped(
    user,
    device,
    second_device,
):
    today = timezone.now().date()

    own_reading = SensorReading.objects.create(
        temperature=22.0,
        humidity=50.0,
        light=65.0,
        water_level=35.0,
        gas=8.0,
        device_id=device.device_id,
    )

    SensorReading.objects.create(
        temperature=90.0,
        humidity=90.0,
        light=90.0,
        water_level=90.0,
        gas=90.0,
        device_id=second_device.device_id,
    )

    rows = list(
        get_readings_for_date(
            user,
            today,
        )
    )

    assert len(rows) == 1

    assert rows[0].id == own_reading.id
