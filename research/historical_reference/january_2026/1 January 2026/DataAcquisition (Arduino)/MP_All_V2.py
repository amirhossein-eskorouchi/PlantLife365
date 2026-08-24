import camera
import time
import machine
import dht
import ujson  # For structured data sending

# -------- SENSORS --------
dht_sensor = dht.DHT11(machine.Pin(15))      # GPIO15 temp, hum
adc = machine.ADC(machine.Pin(33))           # GPIO33 light
adc.atten(machine.ADC.ATTN_11DB)

# -------- CAMERA --------
camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)

print("=== DATA LOGGER STARTED ===")
print("Format: {'temp': X, 'hum': Y, 'light': Z, 'image_size': N}")

# -------- MAIN LOOP --------
counter = 0
while True:
    counter += 1
    
    # 1. COLLECT DATA POINT
    print("--- Collecting data point", counter, "---")
    
    # Sensors
    try:
        dht_sensor.measure()
        temp = dht_sensor.temperature()
        hum = dht_sensor.humidity()
    except:
        temp = hum = -999
    
    try:
        light = adc.read()
    except:
        light = -1
    
    # Image
    buf = camera.capture()
    img_size = len(buf) if buf else 0
    
    # 2. SEND TO COMPUTER (structured JSON)
    data_point = {
        'counter': counter,
        'timestamp': time.ticks_ms(),
        'temp': temp,
        'humidity': hum,
        'light': light,
        'image_size': img_size
    }
    
    # Send JSON data
    print("DATA:", ujson.dumps(data_point))
    
    # 3. Send raw image bytes (if captured)
    if buf:
        print("IMAGE_START:", len(buf))  # Marker + size
        print(buf)  # Raw bytes over serial
        print("IMAGE_END")  # Marker
    
    print("--- Data point", counter, "sent ---")
    
    # 4. Wait before next collection
    time.sleep(10)
