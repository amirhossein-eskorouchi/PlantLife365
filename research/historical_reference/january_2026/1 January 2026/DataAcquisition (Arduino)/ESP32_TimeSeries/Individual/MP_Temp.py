import time
import machine
import dht
import os

# -------- CONFIG --------
SAMPLE_INTERVAL = 2      # Seconds between samples
CSV_PATH = "/temperature.csv"

# -------- DHT SENSOR ONLY --------
print("Init DHT11 on GPIO15...")
dht_sensor = dht.DHT11(machine.Pin(15))
print("DHT11 OK")

# -------- CSV HEADER (TEMP ONLY) --------
try:
    os.stat(CSV_PATH)
    print("CSV file exists")
except OSError:
    try:
        with open(CSV_PATH, "w") as f:
            f.write("timestamp_ms,temp_c\n")
        print("Created CSV header")
    except OSError as e:
        print("CSV header FAILED:", e)

# -------- MAIN LOOP --------
counter = 0
print("Starting temperature logging loop...")

while True:
    counter += 1

    # ---- Read temperature ----
    try:
        dht_sensor.measure()
        temp = dht_sensor.temperature()
    except Exception as e:
        print("DHT read FAILED:", e)
        temp = -999

    # ---- Append to CSV (timestamp + temp) ----
    timestamp = time.ticks_ms()
    line = "%d,%s\n" % (timestamp, temp)

    try:
        with open(CSV_PATH, "a") as f:
            f.write(line)
            f.flush()
        print("#%d: T=%s°C" % (counter, temp))
    except OSError as e:
        print("CSV write failed:", e)

    time.sleep(SAMPLE_INTERVAL)
