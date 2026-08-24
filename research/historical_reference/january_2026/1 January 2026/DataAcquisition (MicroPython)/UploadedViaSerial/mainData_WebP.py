# Libraries
import serial
import json
import base64
import csv
import os
import numpy as np
from datetime import date
import cv2

# WEBP COMPRESSION QUALITY (0-100, higher = better quality, larger files)
WEBP_QUALITY = 90  # Adjust: 95=excellent, 85=good, 75=smaller files

PORT = '/dev/ttyUSB0'  # Change to COM3 on Windows
DIR = f'{date.today()}_Data_WebP_{WEBP_QUALITY}'
CSV_PATH = os.path.join(DIR, f'{date.today()}_timeseries.csv')

# Create DATA directory if it doesn't exist
os.makedirs(DIR, exist_ok=True)

# CSV setup
file_exists = os.path.exists(CSV_PATH)
csv_file = open(CSV_PATH, 'a', newline='')
writer = csv.writer(csv_file)
if not file_exists:
    writer.writerow(['counter', 'timestamp_ms', 'temp_c', 'humidity_pct', 'light_raw', 'image_size_bytes'])

ser = serial.Serial(PORT, 115200, timeout=5)
last_counter = 0
image_buffer = ""
expected_size = 0
in_image = False

print(f"Listening for data... (WebP quality: {WEBP_QUALITY}/100)")

try:
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue

        print(f"[DEBUG] Received: '{line}'")  # DEBUG: See all lines

        # Handle JSON data
        if line.startswith('DATA:'):
            try:
                data = json.loads(line[5:])
                print(f"✓ DATA #{data['counter']}: {data['temp']}°C {data['humidity']}% light={data['light']} size={data['image_size']}")
                
                # Save to CSV
                writer.writerow([data['counter'], data['timestamp'], data['temp'], 
                               data['humidity'], data['light'], data['image_size']])
                csv_file.flush()
                last_counter = data['counter']
                expected_size = data['image_size']
                image_buffer = ""
                in_image = False
                
            except json.JSONDecodeError as e:
                print("✗ JSON error:", e)

        # Start collecting image
        elif line.startswith('IMAGE_START:'):
            try:
                size = int(line.split(':', 1)[1])
                image_buffer = ""
                in_image = True
                print(f"✓ IMAGE_START: expecting {size} bytes ({expected_size} from JSON)")
            except ValueError:
                print("✗ Bad IMAGE_START")

        # End of image
        elif line.startswith('IMAGE_END') and in_image:
            print(f"✓ IMAGE_END: buffer length={len(image_buffer)}")
            try:
                img_data = base64.b64decode(image_buffer)
                print(f"✓ Decoded: {len(img_data)} bytes (expected {expected_size})")
                
                if len(img_data) == expected_size:
                    # Convert JPEG bytes to OpenCV image
                    nparr = np.frombuffer(img_data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if img is not None:
                        filename = f"img_{last_counter}.webp"
                        image_path = os.path.join(DIR, filename)
                        
                        # Save as WebP with configurable quality
                        params = [cv2.IMWRITE_WEBP_QUALITY, WEBP_QUALITY]
                        success = cv2.imwrite(image_path, img, params)
                        
                        if success:
                            print(f"✓ SAVED WEBP: {image_path} (quality {WEBP_QUALITY}/100)")
                        else:
                            print(f"✗ Failed to save WebP: {image_path}")
                    else:
                        print("✗ Failed to decode JPEG to OpenCV image")
                else:
                    print(f"✗ Size mismatch: {len(img_data)} != {expected_size}")
                    
            except Exception as e:
                print("✗ Decode error:", e)
                print(f"Buffer preview: {image_buffer[:100]}...")
            
            image_buffer = ""
            in_image = False
            expected_size = 0

        # Accumulate base64 lines (ONLY when in_image=True)
        elif in_image:
            image_buffer += line + "\n"
            print(f"[BASE64] Added {len(line)} chars, total={len(image_buffer)}")

        elif line == "NO_IMAGE":
            print("✓ No image this cycle")

finally:
    csv_file.close()
    ser.close()