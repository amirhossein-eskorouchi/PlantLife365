import time
import machine
import dht
import os

# -------- CONFIG --------
SAMPLE_INTERVAL = 2      # Seconds between samples
CSV_PATH = "/humidity.csv"

# -------- DHT SENSOR (HUMIDITY ONLY) --------
print("Init DHT11 on GPIO15...")
dht_sensor = dht.DHT11(machine.Pin(15))
print("DHT11 OK")

# -------- CSV HEADER (HUMIDITY ONLY) --------
try:
    os.stat(CSV_PATH)
    print("CSV file exists")
except OSError:
    try:
        with open(CSV_PATH, "w") as f:
            f.write("timestamp_ms,humidity_pct\n")
        print("Created CSV header")
    except OSError as e:
        print("CSV header FAILED:", e)

# -------- MAIN LOOP --------
counter = 0
print("Starting humidity logging loop...")

while True:
    counter += 1

    # ---- Read humidity ----
    try:
        dht_sensor.measure()
        hum = dht_sensor.humidity()
    except Exception as e:
        print("DHT read FAILED:", e)
        hum = -1

    # ---- Append to CSV (timestamp + humidity) ----
    timestamp = time.ticks_ms()
    line = "%d,%s\n" % (timestamp, hum)

    try:
        with open(CSV_PATH, "a") as f:
            f.write(line)
            f.flush()
        print("#%d: H=%s%%" % (counter, hum))
    except OSError as e:
        print("CSV write failed:", e)

    time.sleep(SAMPLE_INTERVAL)
