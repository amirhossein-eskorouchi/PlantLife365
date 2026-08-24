import camera
import time
import machine
import dht
import os

# -------- CONFIG --------
SAVE_IMAGES = True      # True = save img_#.jpg to internal flash
SAMPLE_INTERVAL = 10     # Sampling period in seconds

# -------- SENSORS --------
print("Init DHT and ADC...")
dht_sensor = dht.DHT11(machine.Pin(15))      # GPIO15 for DHT11
adc = machine.ADC(machine.Pin(33))           # GPIO33 for LDR/light sensor
adc.atten(machine.ADC.ATTN_11DB)
print("Sensors OK")

# -------- CAMERA (OPTIONAL) --------
camera_ok = False
try:
    print("Init camera...")
    camera.init(0)
    camera.framesize(camera.FRAMESIZE_QQVGA)
    camera_ok = True
    print("Camera OK")
except Exception as e:
    print("Camera init FAILED:", e)
    # Script continues; only sensor logging will work

# -------- CSV FILE SETUP --------
csv_path = '/sensors.csv'
try:
    os.stat(csv_path)
    print("CSV file exists")
except OSError:
    try:
        with open(csv_path, 'w') as f:
            f.write('timestamp_ms,temp,humidity,light\n')
        print("Created CSV header")
    except OSError as e:
        print("CSV header create FAILED:", e)

# -------- MAIN LOOP --------
counter = 0
print("Starting offline logging loop...")

while True:
    counter += 1
    print("Loop", counter)

    # ---- Optional image capture ----
    if camera_ok and SAVE_IMAGES:
        try:
            buf = camera.capture()
            if buf:
                img_path = '/img_%d.jpg' % counter
                try:
                    with open(img_path, 'wb') as f:
                        f.write(buf)
                    print("Saved", img_path)
                except OSError as e:
                    print("Image save failed:", e)
        except Exception as e:
            print("Camera capture FAILED:", e)

    # ---- Read sensors ----
    try:
        dht_sensor.measure()
        temp = dht_sensor.temperature()
        hum = dht_sensor.humidity()
    except Exception as e:
        print("DHT read FAILED:", e)
        temp = hum = -999

    try:
        light = adc.read()
    except Exception as e:
        print("ADC read FAILED:", e)
        light = -1

    # ---- Append to CSV ----
    timestamp = time.ticks_ms()
    line = "%d,%s,%s,%s\n" % (timestamp, temp, hum, light)

    try:
        with open(csv_path, 'a') as f:
            f.write(line)
            f.flush()
        print("#%d -> T=%s°C H=%s%% Light=%s" %
              (counter, temp, hum, light))
    except OSError as e:
        print("CSV write failed:", e)

    # ---- Wait until next sample ----
    time.sleep(SAMPLE_INTERVAL)
