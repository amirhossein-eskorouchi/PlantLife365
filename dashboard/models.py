from django.db import models # type: ignore
from django.contrib.auth.models import User # type: ignore
# Create your models here.
class SensorReading(models.Model):
    temperature = models.FloatField(default=0.0)
    humidity = models.FloatField(default=0.0)
    light = models.IntegerField(default=0)
    water_level = models.FloatField(default=0.0)
    gas = models.FloatField(default=0.0)
    device_id = models.CharField(max_length=100, blank=True, null=True) # Optional link to HardwareDevice
    image = models.ImageField(upload_to='sensor_images/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # this makes it readable in the admin panel
        return f"Temperature: {self.temperature}, Humidity: {self.humidity}, Light: {self.light}, Water: {self.water_level}, Gas: {self.gas} at {self.timestamp}"

class SystemLog(models.Model):
    LEVEL_CHOICES = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
    ]
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='INFO')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp'] # Newest first

    def __str__(self):
        return f"[{self.level}] {self.message} at {self.timestamp}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    has_seen_intro = models.BooleanField(default=False)
    # We remove device_id from UserProfile because a User can theoretically own multiple HardwareDevices

    def __str__(self):
        return self.user.username

class HardwareDevice(models.Model):
    device_id = models.CharField(max_length=100, unique=True)
    secret_pin = models.CharField(max_length=20)
    name = models.CharField(max_length=100, blank=True, null=True, help_text="Custom name or location")
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device_id} (Owned by: {self.owner.username if self.owner else 'Unclaimed'})"

class UserSubscription(models.Model):
    TIERS = (
        ('STD', 'Standard'),
        ('RES', 'Researcher'),
        ('PRM', 'Premium'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    tier = models.CharField(max_length=10, choices=TIERS, default='STD')
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    max_devices = models.IntegerField(default=1) # Free tier default

    def __str__(self):
        return f"{self.user.username} - {self.get_tier_display()} (Max Devices: {self.max_devices})"