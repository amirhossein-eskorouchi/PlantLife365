# Libraries
import network  # type: ignore
import ujson    # type: ignore
import camera   # type: ignore
import time     # type: ignore
import machine  # type: ignore
import dht      # type: ignore
import socket   # type: ignore
import gc

# ========== CONFIGURATION ==========
try:
    from config import (
        WIFI_SSID,
        WIFI_PASS,
        PC_IP,
        PC_PORT,
        DEVICE_ID,
    )
except ImportError:
    raise RuntimeError(
        "Missing config.py. Copy config.example.py to config.py "
        "and set device-specific values."
    )

print("ESP32 Data Logger")

# ========== CONNECT TO WIFI ==========
wlan = network.WLAN(network.AP_IF)
wlan.active(True)
try:
    wlan.config(essid=WIFI_SSID, password=WIFI_PASS, authmode=3)
except Exception as e:
    print("Config error (ignore if hotspot works)", e)
time.sleep(3)
print('Hotspot Active. Connect your PC to "ESP32".')
print('ESP32 IP info:', wlan.ifconfig())

# ========== SENSORS SETUP ==========
dht_sensor = dht.DHT11(machine.Pin(15))
adc = machine.ADC(machine.Pin(33))
adc.atten(machine.ADC.ATTN_11DB)
water = machine.ADC(machine.Pin(36))
water.atten(machine.ADC.ATTN_11DB)
g = machine.ADC(machine.Pin(32))
g.atten(machine.ADC.ATTN_11DB)

# ========== CAMERA SETUP ==========
try:
    camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
    camera.quality(80)                    
    print("Camera initialized")
except Exception as e:
    print("Camera init error:", e)

# ========== SEND DATA FUNCTION ==========
def send_report(data_dict, image_data):
    boundary = "esp32boundary"
    boundary_bytes = boundary.encode()

    parts = []

    # JSON part
    parts.append(b"--" + boundary_bytes)
    parts.append(b'Content-Disposition: form-data; name="data"')
    parts.append(b"")
    parts.append(ujson.dumps(data_dict).encode())

    # Image part (optional)
    if image_data:
        parts.append(b"--" + boundary_bytes)
        parts.append(b'Content-Disposition: form-data; name="image"; filename="frame.jpg"')
        parts.append(b"Content-Type: image/jpeg")
        parts.append(b"")
        parts.append(image_data)

    parts.append(b"--" + boundary_bytes + b"--")
    parts.append(b"")

    body = b"\r\n".join(parts)

    headers = b""
    headers += b"POST /upload HTTP/1.1\r\n"
    headers += b"Host: " + PC_IP.encode() + b":" + str(PC_PORT).encode() + b"\r\n"
    headers += b"Content-Type: multipart/form-data; boundary=" + boundary_bytes + b"\r\n"
    headers += b"Content-Length: " + str(len(body)).encode() + b"\r\n"
    headers += b"Connection: close\r\n\r\n"

    try:
        s = socket.socket()
        s.settimeout(10.0)
        s.connect((PC_IP, PC_PORT))
        # Single send is fine here but body is as small as we can make it
        s.send(headers + body)
        _ = s.recv(128)
        s.close()
        print("Sent successfully!")
        return True
    except Exception as e:
        print("Failed to send:", e)
        return False
    finally:
        # Explicitly drop big buffers to help GC and reduce fragmentation on ESP32 [web:12][web:18]
        body = None
        parts = None
        gc.collect()

# Optional: dedicated streaming function if you want imageâ€‘only, chunked
def send_image_only(image_data):
    boundary = "esp32boundary"
    boundary_bytes = boundary.encode()

    headers = []
    headers.append("POST /upload-image HTTP/1.1")
    headers.append("Host: {}:{}".format(PC_IP, PC_PORT))
    headers.append("Content-Type: multipart/form-data; boundary={}".format(boundary))
    # Simple length estimate (OK because we control both ends)
    content_length = len(image_data) + 200
    headers.append("Content-Length: {}".format(content_length))
    headers.append("Connection: close")
    headers.append("")
    headers_bytes = ("\r\n".join(headers)).encode()

    try:
        s = socket.socket()
        s.settimeout(10.0)
        s.connect((PC_IP, PC_PORT))
        s.send(headers_bytes)

        s.send(b"--" + boundary_bytes + b"\r\n")
        s.send(b'Content-Disposition: form-data; name="image"; filename="frame.jpg"\r\n')
        s.send(b"Content-Type: image/jpeg\r\n\r\n")

        chunk_size = 4096
        for i in range(0, len(image_data), chunk_size):
            s.send(image_data[i:i+chunk_size])

        s.send(b"\r\n--" + boundary_bytes + b"--\r\n")
        s.close()
        return True
    except Exception as e:
        print("Image send failed:", e)
        return False

# ========== MAIN LOOP ==========
counter = 0
while True:
    counter += 1
    print("\n--- Report #{} ---".format(counter))

    dht_sensor.measure()
    temp = round(dht_sensor.temperature(), 2)
    hum = round(dht_sensor.humidity(), 2)

    light_val = adc.read()
    light_pct = round((light_val / 4095) * 100, 2)

    water_val = water.read()
    water_pct = round((water_val / 4095) * 100, 2)

    gas_val = g.read()
    gas_pct = round((gas_val / 4095) * 100, 2)

    print("Sensors: T={}C H={}% L={}% W={}% G={}%".format(temp, hum, light_pct, water_pct, gas_pct))

    buf = None
    try:
        buf = camera.capture()
        img_size = len(buf) if buf else 0
        print("Photo taken:", len(buf), "bytes")
    except Exception as e:
        print("Capture error:", e)
        img_size = 0

    data_point = {
        "device_id": DEVICE_ID,
        "temp": temp,
        "humidity": hum,
        "light": light_pct,
        "water_level": water_pct,
        "gas": gas_pct,
    }

    # Send JSON + image (if any)
    send_report(data_point, buf)

    # Drop JPEG immediately after use
    buf = None
    gc.collect()
    time.sleep(1)
