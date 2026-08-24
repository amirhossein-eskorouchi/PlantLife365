import time
import machine
import os

# -------- CONFIG --------
SAMPLE_INTERVAL = 2      # Seconds between samples
CSV_PATH = "/light.csv"

# -------- LIGHT SENSOR (ADC ONLY) --------
print("Init ADC light sensor on GPIO33...")
adc = machine.ADC(machine.Pin(33))       # GPIO33 for LDR/light sensor
adc.atten(machine.ADC.ATTN_11DB)         # Full range 0-3.3V
print("Light sensor OK")

# -------- CSV HEADER (LIGHT ONLY) --------
try:
    os.stat(CSV_PATH)
    print("CSV file exists")
except OSError:
    try:
        with open(CSV_PATH, "w") as f:
            f.write("timestamp_ms,light_raw\n")
        print("Created CSV header")
    except OSError as e:
        print("CSV header FAILED:", e)

# -------- MAIN LOOP --------
counter = 0
print("Starting light logging loop...")

while True:
    counter += 1

    # ---- Read light sensor ----
    try:
        light = adc.read()
    except Exception as e:
        print("ADC read FAILED:", e)
        light = -1

    # ---- Append to CSV (timestamp + light raw value) ----
    timestamp = time.ticks_ms()
    line = "%d,%s\n" % (timestamp, light)

    try:
        with open(CSV_PATH, "a") as f:
            f.write(line)
            f.flush()
        print("#%d: Light=%s" % (counter, light))
    except OSError as e:
        print("CSV write failed:", e)

    time.sleep(SAMPLE_INTERVAL)
