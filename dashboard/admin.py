from django.contrib import admin # type: ignore

# Register your models here.
from .models import SensorReading

admin.site.register(SensorReading)