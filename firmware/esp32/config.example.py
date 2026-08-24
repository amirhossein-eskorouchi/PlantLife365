"""
PlantLife365 ESP32/MicroPython configuration example.

Copy this file to:

    config.py

on the ESP32 and replace the placeholder values.

Never commit the real config.py.
"""

WIFI_SSID = "PlantLife365-Device"

WIFI_PASS = "CHANGE_ME_WIFI_PASSWORD"

PC_IP = "192.168.4.2"

PC_PORT = 8000

DEVICE_ID = "plantlife365-device-001"

# Must match the Device Password / Secret PIN associated with
# the corresponding HardwareDevice in Django.
DEVICE_TOKEN = "CHANGE_ME_DEVICE_SECRET"
