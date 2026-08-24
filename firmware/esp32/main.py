# PlantLife365 ESP32/MicroPython telemetry firmware

import gc
import socket
import time

import camera  # type: ignore
import dht  # type: ignore
import machine  # type: ignore
import network  # type: ignore
import ujson  # type: ignore


# ============================================================
# LOCAL DEVICE CONFIGURATION
# ============================================================

try:
    from config import (
        WIFI_SSID,
        WIFI_PASS,
        PC_IP,
        PC_PORT,
        DEVICE_ID,
        DEVICE_TOKEN,
    )

except ImportError:
    raise RuntimeError(
        "Missing config.py. Copy config.example.py to config.py "
        "and set the device-specific values."
    )


print(
    "PlantLife365 ESP32 Data Logger"
)


# ============================================================
# WI-FI ACCESS POINT
# ============================================================

wlan = network.WLAN(
    network.AP_IF
)

wlan.active(
    True
)

try:
    wlan.config(
        essid=WIFI_SSID,
        password=WIFI_PASS,
        authmode=3,
    )

except Exception as exc:
    print(
        "Wi-Fi configuration error:",
        exc,
    )

time.sleep(
    3
)

print(
    "PlantLife365 hotspot active."
)

print(
    "ESP32 IP information:",
    wlan.ifconfig(),
)


# ============================================================
# SENSOR SETUP
# ============================================================

dht_sensor = dht.DHT11(
    machine.Pin(15)
)

light_adc = machine.ADC(
    machine.Pin(33)
)

light_adc.atten(
    machine.ADC.ATTN_11DB
)

water_adc = machine.ADC(
    machine.Pin(36)
)

water_adc.atten(
    machine.ADC.ATTN_11DB
)

gas_adc = machine.ADC(
    machine.Pin(32)
)

gas_adc.atten(
    machine.ADC.ATTN_11DB
)


# ============================================================
# CAMERA SETUP
# ============================================================

try:

    camera.init(
        0,
        format=camera.JPEG,
        fb_location=camera.PSRAM,
    )

    camera.quality(
        80
    )

    print(
        "Camera initialized"
    )

except Exception as exc:

    print(
        "Camera initialization error:",
        exc,
    )


# ============================================================
# SEND TELEMETRY
# ============================================================

def send_report(
    data_dict,
    image_data,
):

    boundary = "esp32boundary"

    boundary_bytes = boundary.encode()

    parts = []

    parts.append(
        b"--"
        + boundary_bytes
    )

    parts.append(
        b'Content-Disposition: form-data; name="data"'
    )

    parts.append(
        b""
    )

    parts.append(
        ujson.dumps(
            data_dict
        ).encode()
    )

    if image_data:

        parts.append(
            b"--"
            + boundary_bytes
        )

        parts.append(
            b'Content-Disposition: form-data; '
            b'name="image"; filename="frame.jpg"'
        )

        parts.append(
            b"Content-Type: image/jpeg"
        )

        parts.append(
            b""
        )

        parts.append(
            image_data
        )

    parts.append(
        b"--"
        + boundary_bytes
        + b"--"
    )

    parts.append(
        b""
    )

    body = b"\r\n".join(
        parts
    )

    headers = b""

    headers += (
        b"POST /upload HTTP/1.1\r\n"
    )

    headers += (
        b"Host: "
        + PC_IP.encode()
        + b":"
        + str(
            PC_PORT
        ).encode()
        + b"\r\n"
    )

    headers += (
        b"X-PlantLife365-Token: "
        + DEVICE_TOKEN.encode()
        + b"\r\n"
    )

    headers += (
        b"Content-Type: multipart/form-data; boundary="
        + boundary_bytes
        + b"\r\n"
    )

    headers += (
        b"Content-Length: "
        + str(
            len(body)
        ).encode()
        + b"\r\n"
    )

    headers += (
        b"Connection: close\r\n\r\n"
    )

    sock = None

    try:

        sock = socket.socket()

        sock.settimeout(
            10.0
        )

        sock.connect(
            (
                PC_IP,
                PC_PORT,
            )
        )

        sock.send(
            headers
            + body
        )

        response = sock.recv(
            256
        )

        print(
            "Server response:",
            response,
        )

        print(
            "Telemetry sent successfully."
        )

        return True

    except Exception as exc:

        print(
            "Telemetry send failed:",
            exc,
        )

        return False

    finally:

        if sock is not None:

            try:
                sock.close()

            except Exception:
                pass

        body = None
        parts = None

        gc.collect()


# ============================================================
# MAIN LOOP
# ============================================================

counter = 0

while True:

    counter += 1

    print(
        "\n--- Report #{} ---".format(
            counter
        )
    )

    try:

        dht_sensor.measure()

        temperature = round(
            dht_sensor.temperature(),
            2,
        )

        humidity = round(
            dht_sensor.humidity(),
            2,
        )

    except Exception as exc:

        print(
            "DHT sensor error:",
            exc,
        )

        time.sleep(
            1
        )

        continue

    light_raw = light_adc.read()

    light_percent = round(
        (light_raw / 4095) * 100,
        2,
    )

    water_raw = water_adc.read()

    water_percent = round(
        (water_raw / 4095) * 100,
        2,
    )

    gas_raw = gas_adc.read()

    gas_percent = round(
        (gas_raw / 4095) * 100,
        2,
    )

    print(
        "Sensors: "
        "T={}C "
        "H={}% "
        "L={}% "
        "W={}% "
        "G={}%".format(
            temperature,
            humidity,
            light_percent,
            water_percent,
            gas_percent,
        )
    )

    image_buffer = None

    try:

        image_buffer = camera.capture()

        if image_buffer:

            print(
                "Photo captured:",
                len(
                    image_buffer
                ),
                "bytes",
            )

    except Exception as exc:

        print(
            "Camera capture error:",
            exc,
        )

        image_buffer = None

    data_point = {
        "device_id": DEVICE_ID,
        "temp": temperature,
        "humidity": humidity,
        "light": light_percent,
        "water_level": water_percent,
        "gas": gas_percent,
    }

    send_report(
        data_point,
        image_buffer,
    )

    image_buffer = None

    gc.collect()

    time.sleep(
        1
    )
