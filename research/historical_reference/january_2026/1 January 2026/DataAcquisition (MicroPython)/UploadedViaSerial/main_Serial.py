import camera
import time
import machine
import dht
import ujson
import ubinascii

# -------- SENSORS --------
dht_sensor = dht.DHT11(machine.Pin(15))      # GPIO15 temp, hum
adc = machine.ADC(machine.Pin(33))           # GPIO33 light
adc.atten(machine.ADC.ATTN_11DB)

# -------- ESP32-CAM or ESP32-EXT --------
camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)

print("DATA LOGGER STARTED")
print("Format: {'temp': XX.XX, 'humidity': YY.YY, 'light': ZZ.ZZ, 'image_size': N}")

# -------- MAIN LOOP --------
counter = 0
while True:
    counter += 1
    
    # 1. COLLECT DATA POINT
    print("--- Collecting data point", counter, "---")
    
    # Sensors - 2 decimal places
    try:
        dht_sensor.measure()
        temp = round(float(dht_sensor.temperature()), 2)     # Ensure float, 2 decimals
        hum  = round(float(dht_sensor.humidity()), 2)        # Ensure float, 2 decimals
    except Exception as e:
        print("DHT error:", e)
        temp = hum = -999.00
    
    # Light sensor - corrected (higher ADC = brighter for standard wiring)
    try:
        raw_adc = adc.read()
        light = round(100.0 - (raw_adc / 4095.0 * 100.0), 2)
    except Exception as e:
        print("ADC error:", e)
        light = -999.00
    
    # Image
    buf = None
    try:
        buf = camera.capture()
    except Exception as e:
        print("Camera capture error:", e)

    img_size = len(buf) if buf else 0

    # 2. SEND JSON DATA
    data_point = {
        "counter":   counter,
        "timestamp": time.ticks_ms(),
        "temp":      float(temp),      # Ensure JSON serializable float
        "humidity":  float(hum),       # Ensure JSON serializable float
        "light":     float(light),     # Ensure JSON serializable float
        "image_size": img_size,
    }
    print("DATA:", ujson.dumps(data_point))

    # 3. Send image as base64 (if captured)
    if buf and img_size > 0:
        try:
            img_b64 = ubinascii.b2a_base64(buf).decode().strip()
            print("IMAGE_START:", img_size)
            print(img_b64)
            print("IMAGE_END")
        except Exception as e:
            print("Image encoding error:", e)
    else:
        print("NO_IMAGE")

    print("--- Data point", counter, "sent ---")
    time.sleep(10)  # 0.1 Hz