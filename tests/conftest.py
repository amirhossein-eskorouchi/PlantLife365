import pytest

from django.contrib.auth.models import User

from dashboard.models import HardwareDevice


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="plantlife365_user",
        email="user@example.com",
        password="test-password-123",
    )


@pytest.fixture
def second_user(db):
    return User.objects.create_user(
        username="plantlife365_user_2",
        email="user2@example.com",
        password="test-password-456",
    )


@pytest.fixture
def device(user):
    hardware = HardwareDevice(
        device_id="plantlife365-device-001",
        owner=user,
        is_active=True,
    )

    hardware.set_secret_pin(
        "device-secret-001"
    )

    hardware.save()

    return hardware


@pytest.fixture
def second_device(second_user):
    hardware = HardwareDevice(
        device_id="plantlife365-device-002",
        owner=second_user,
        is_active=True,
    )

    hardware.set_secret_pin(
        "device-secret-002"
    )

    hardware.save()

    return hardware
