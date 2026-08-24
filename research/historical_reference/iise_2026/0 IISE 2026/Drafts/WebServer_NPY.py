from flask import Flask, Response, render_template, jsonify
import cv2
import os
from datetime import datetime
import csv
import time
import requests
import numpy as np
import threading
import queue

app = Flask(__name__)

# Initialize photo paths
base_path = "/home/siol1/Documents/Prototype"

# Ensure output directory exists
os.makedirs(base_path, exist_ok=True)

# Quick startup write test to verify we can create files in base_path
def _startup_write_test(path):
    test_path = os.path.join(path, '.save_test')
    try:
        with open(test_path, 'wb') as tf:
            tf.write(b'test')
            tf.flush(); os.fsync(tf.fileno())
        exists = os.path.exists(test_path)
        size = os.path.getsize(test_path) if exists else 0
        print(f"Startup write test: exists={exists}, size={size}, path={test_path}")
        try:
            os.remove(test_path)
        except Exception:
            pass
    except Exception as e:
        print(f"Startup write test FAILED for {test_path}: {e}")


_startup_write_test(base_path)

# --- Permissions and diagnostics helper ---------------------------------
def _check_directory_permissions(path):
    try:
        st = os.stat(path)
        writable = os.access(path, os.W_OK)
        print(f"Save directory: {path}")
        print(f" - owner uid: {st.st_uid}, gid: {st.st_gid}")
        print(f" - mode: {oct(st.st_mode)}")
        print(f" - writable by current process: {writable}")
        if not writable:
            print("Suggestion: make the directory writable, for example:")
            print(f"  sudo chown $USER:{st.st_gid} {path}  # change owner")
            print(f"  sudo chmod u+w {path}  # add write permission for owner")
    except Exception as e:
        print(f"Could not stat directory {path}: {e}")


# run diagnostics at startup
_check_directory_permissions(base_path)

# Save rate limiter (seconds)
SAVE_INTERVAL_S = 10.0

# Retrieve IP
ip = '192.168.4.1'

# Default URL
url = f'http://{ip}/cam-mid.jpg'
signals_url = f'http://{ip}/signals'

# CSV logging setup
date_str = datetime.now().strftime("%Y%m%d")
csv_filename = os.path.join(base_path, f'{date_str}_DetectionLog.csv')

# Create CSV file with header if not exist
if not os.path.exists(csv_filename):
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time', 'Temperature', 'Humidity', 'SoilMoisture', 'Radiation'])


def get_sensor_data(timeout=None):
    """Fetch temperature and humidity from ESP32 /signals endpoint"""
    if timeout is None:
        timeout = SAVE_INTERVAL_S
    try:
        response = requests.get(signals_url, timeout=timeout)
        if response.status_code == 200:
            # Try JSON first
            try:
                j = response.json()
                if isinstance(j, dict):
                    temp = float(j.get('temperature') or j.get('temp') or j.get('t') or 0)
                    humidity = float(j.get('humidity') or j.get('h') or 0)
                    soilMoist = float(j.get('soilMoist') or j.get('soil') or 0)
                    radiation = float(j.get('radiation') or j.get('rad') or 0)
                    return temp, humidity, soilMoist, radiation
                elif isinstance(j, (list, tuple)) and len(j) >= 4:
                    return float(j[0]), float(j[1]), float(j[2]), float(j[3])
            except Exception:
                data = [p.strip() for p in response.text.split(',') if p.strip()!='']
                vals = [None, None, None, None]
                for i in range(min(len(data), 4)):
                    try:
                        vals[i] = float(data[i])
                    except Exception:
                        vals[i] = None
                return tuple(vals)
        else:
            print(f"get_sensor_data: non-200 response: {response.status_code}")
    except Exception as e:
        print(f"Error fetching sensor data: {e}")
    return None, None, None, None


# Background save queue + worker (single shared worker for all clients)
save_queue = queue.Queue(maxsize=400)

class SaveWorker(threading.Thread):
    def __init__(self, q):
        super().__init__(daemon=True)
        self.q = q

    def run(self):
        while True:
            item = self.q.get()
            if item is None:
                self.q.task_done()
                break
            path, arr = item
            try:
                tmp = path + '.tmp'
                # write numpy array to temporary file then atomically rename
                np.save(tmp, arr)
                os.replace(tmp, path)
                print(f"SaveWorker: wrote npy {path}")
            except Exception as e:
                print(f"SaveWorker error writing {path}: {e}")
            finally:
                self.q.task_done()


# start worker
_save_worker = SaveWorker(save_queue)
_save_worker.start()


def generate_frames():
    """Fetch a single-JPEG endpoint and stream MJPEG; schedule .npy saves asynchronously."""
    session = requests.Session()
    last_save_time = 0.0
    SAVE_AS_NUMPY = False
    FRAME_SLEEP = 5

    while True:
        try:
            try:
                resp = session.get(url, timeout=2.0)
            except Exception as e:
                print(f"HTTP frame fetch error: {e}")
                time.sleep(0.2)
                continue

            if resp.status_code != 200 or not resp.content:
                print(f"HTTP frame non-200 or empty: {resp.status_code}")
                time.sleep(0.2)
                continue

            # stream the original JPEG bytes (no re-encode)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + resp.content + b'\r\n')

            # Decode and schedule .npy save (non-blocking)
            if SAVE_AS_NUMPY:
                try:
                    arr = np.frombuffer(resp.content, np.uint8)
                    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        now = time.time()
                        if now - last_save_time >= SAVE_INTERVAL_S:
                            ts = datetime.now().strftime("%H.%M.%S.%f")
                            npy_path = os.path.join(base_path, f"Frame_{ts}.npy")
                            try:
                                save_queue.put_nowait((npy_path, frame.copy()))
                            except queue.Full:
                                print("save_queue full; dropping frame save")
                            last_save_time = now
                except Exception as e:
                    print(f"Decode/save scheduling error: {e}")

            time.sleep(FRAME_SLEEP)

        except Exception as e:
            print(f"Stream generation error: {e}")
            time.sleep(0.5)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/sensor_data')
def sensor_data():
    """Return current temperature and humidity as JSON"""
    temp, humidity, soilMoist, radiation = get_sensor_data()
    return jsonify({
        'temperature': temp,
        'humidity': humidity,
        'soilMoist': soilMoist,
        'radiation': radiation,
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)