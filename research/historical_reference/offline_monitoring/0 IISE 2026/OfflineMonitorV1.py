import os
import csv
import cv2
import time
import requests
import numpy as np
from datetime import datetime

ESP_IP = "192.168.4.1"
SIGNAL_URL = f"http://{ESP_IP}/signals"
CAM_URL = f"http://{ESP_IP}/cam-mid.jpg"

csv_path = "PROJECT_ROOT/timeseries.csv"
frame_save_dir = "PROJECT_ROOT/frames"
os.makedirs(frame_save_dir, exist_ok=True)

# Prepare CSV file with header
with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["timestamp", "tempC", "humidity", "soilMoist", "uSv_h"])

timeout = 10
frame_idx = 0
save_every_n_frames = 5

while True:
    t = datetime.now().strftime("%H:%M:%S")

    # 1) Get signals and append to CSV
    try:
        sig_resp = requests.get(SIGNAL_URL, timeout=timeout)
        sig_resp.raise_for_status()
        line = sig_resp.text.strip()
        parts = line.split(",")
        if len(parts) == 4:
            tempC, hum, soil, usvh = map(float, parts)
            with open(csv_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([t, tempC, hum, soil, usvh])
    except Exception as e:
        print("Signal error:", e)

    # 2) Get image, view live, optionally save as .npy
    try:
        img_resp = requests.get(CAM_URL, timeout=timeout)
        img_resp.raise_for_status()
        img_array = np.asarray(bytearray(img_resp), dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if frame is not None:
            cv2.imshow("ESP32CAM", frame)

            # save every Nth frame as .npy
            if frame_idx % save_every_n_frames == 0:
                np.save(f"{frame_save_dir}/frame_{frame_idx:06d}.npy", frame)

            frame_idx += 1

    except Exception as e:
        print("Image error:", e)

    # exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    # small delay to avoid hammering ESP
    time.sleep(0.1)
