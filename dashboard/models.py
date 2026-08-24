import hmac

from django.contrib.auth.hashers import (
    check_password,
    identify_hasher,
    make_password,
)
from django.contrib.auth.models import User
from django.db import models


class SensorReading(models.Model):
    temperature = models.FloatField(default=0.0)
    humidity = models.FloatField(default=0.0)
    light = models.FloatField(default=0.0)
    water_level = models.FloatField(default=0.0)
    gas = models.FloatField(default=0.0)

    device_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    image = models.ImageField(
        upload_to="sensor_images/",
        blank=True,
        null=True,
    )

    timestamp = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"Temperature: {self.temperature}, "
            f"Humidity: {self.humidity}, "
            f"Light: {self.light}, "
            f"Water: {self.water_level}, "
            f"Gas: {self.gas} "
            f"at {self.timestamp}"
        )


class SystemLog(models.Model):
    LEVEL_CHOICES = [
        ("INFO", "Info"),
        ("WARNING", "Warning"),
        ("CRITICAL", "Critical"),
    ]

    level = models.CharField(
        max_length=10,
        choices=LEVEL_CHOICES,
        default="INFO",
    )

    message = models.TextField()

    timestamp = models.DateTimeField(
        auto_now_add=True
    )

    is_read = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return (
            f"[{self.level}] "
            f"{self.message} "
            f"at {self.timestamp}"
        )


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )

    has_seen_intro = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.user.username


class HardwareDevice(models.Model):
    device_id = models.CharField(
        max_length=100,
        unique=True,
    )

    secret_pin = models.CharField(
        max_length=128,
    )

    name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Custom name or location",
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="devices",
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        owner_name = (
            self.owner.username
            if self.owner
            else "Unclaimed"
        )

        return (
            f"{self.device_id} "
            f"(Owned by: {owner_name})"
        )

    def _pin_is_hashed(self):
        if not self.secret_pin:
            return False

        try:
            identify_hasher(
                self.secret_pin
            )
            return True
        except ValueError:
            return False

    def set_secret_pin(self, raw_pin):
        if not raw_pin:
            raise ValueError(
                "Device secret cannot be empty"
            )

        self.secret_pin = make_password(
            str(raw_pin)
        )

    def check_secret_pin(self, raw_pin):
        """
        Validate a device secret.

        Historical private databases may contain plaintext device PINs.
        Plaintext comparison is retained only for controlled migration.
        """

        if not raw_pin:
            return False

        if not self.secret_pin:
            return False

        raw_pin = str(raw_pin)

        if self._pin_is_hashed():
            return check_password(
                raw_pin,
                self.secret_pin,
            )

        return hmac.compare_digest(
            str(self.secret_pin),
            raw_pin,
        )

    def upgrade_legacy_secret_pin(
        self,
        raw_pin,
    ):
        """
        Upgrade a successfully verified historical plaintext PIN to the
        maintained password-hash representation.
        """

        if self._pin_is_hashed():
            return False

        if not self.check_secret_pin(raw_pin):
            return False

        self.set_secret_pin(
            raw_pin
        )

        return True


class UserSubscription(models.Model):
    TIERS = (
        ("STD", "Standard"),
        ("RES", "Researcher"),
        ("PRM", "Premium"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="subscription",
    )

    tier = models.CharField(
        max_length=10,
        choices=TIERS,
        default="STD",
    )

    stripe_subscription_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    max_devices = models.IntegerField(
        default=1
    )

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.get_tier_display()} "
            f"(Max Devices: {self.max_devices})"
        )
