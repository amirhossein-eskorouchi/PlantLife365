from dashboard.models import HardwareDevice


def test_new_device_secret_is_hashed(db):
    device = HardwareDevice(
        device_id="secure-device-001",
    )

    device.set_secret_pin(
        "my-device-secret"
    )

    assert device.secret_pin != "my-device-secret"

    assert device.check_secret_pin(
        "my-device-secret"
    )

    assert not device.check_secret_pin(
        "incorrect-secret"
    )


def test_legacy_plaintext_secret_can_be_upgraded(db):
    device = HardwareDevice.objects.create(
        device_id="legacy-device-001",
        secret_pin="legacy-secret",
    )

    assert device.check_secret_pin(
        "legacy-secret"
    )

    changed = device.upgrade_legacy_secret_pin(
        "legacy-secret"
    )

    assert changed is True

    assert device.secret_pin != "legacy-secret"

    assert device.check_secret_pin(
        "legacy-secret"
    )


def test_wrong_legacy_secret_is_not_upgraded(db):
    device = HardwareDevice.objects.create(
        device_id="legacy-device-002",
        secret_pin="correct-secret",
    )

    changed = device.upgrade_legacy_secret_pin(
        "wrong-secret"
    )

    assert changed is False

    assert device.secret_pin == "correct-secret"
