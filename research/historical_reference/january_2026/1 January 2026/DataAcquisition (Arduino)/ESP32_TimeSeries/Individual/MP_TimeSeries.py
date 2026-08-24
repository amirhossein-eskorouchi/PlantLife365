import time
import machine
import dht
import os

# -------- CONFIG --------
SAMPLE_INTERVAL = 2      # Seconds between samples
CSV_PATH = "/sensors.csv"

# -------- SENSORS --------
print("Init DHT11 and light sensor...")
dht_sensor = dht.DHT11(machine.Pin(15))      # GPIO15 for DHT11
adc = machine.ADC(machine.Pin(33))           # GPIO33 for light
adc.atten(machine.ADC.ATTN_11DB)
print("Sensors OK")

# -------- CSV HEADER --------
try:
    os.stat(CSV_PATH)
    print("CSV exists")
except OSError:
    try:
        with open(CSV_PATH, "w") as f:
            f.write("timestamp_ms,temp,humidity,light\n")
        print("Created CSV header")
    except OSError as e:
        print("CSV header FAILED:", e)

# -------- MAIN LOOP --------
counter = 0
print("Starting sensor logging...")

while True:
    counter += 1

    # ---- Read DHT (temp + humidity) ----
    try:
        dht_sensor.measure()
        temp = dht_sensor.temperature()
        hum = dht_sensor.humidity()
    except Exception as e:
        print("DHT FAILED:", e)
        temp = hum = -999

    # ---- Read light ----
    try:
        light = adc.read()
    except Exception as e:
        print("Light FAILED:", e)
        light = -1

    # ---- CSV log ----
    timestamp = time.ticks_ms()
    line = "%d,%s,%s,%s\n" % (timestamp, temp, hum, light)

    try:
        with open(CSV_PATH, "a") as f:
            f.write(line)
            f.flush()
        print("#%d: T=%s°C H=%s%% L=%s" % (counter, temp, hum, light))
    except OSError as e:
        print("CSV write failed:", e)

    time.sleep(SAMPLE_INTERVAL)
