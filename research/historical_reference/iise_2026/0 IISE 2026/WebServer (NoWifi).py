from flask import Flask, Response, render_template, jsonify
import cv2
import os
from datetime import datetime
import csv
import time
import requests

app = Flask(__name__)

# Initialize photo paths
base_path = "PROJECT_ROOT/Proto"

# Retrieve IP
ip = '192.168.4.1'

# Default URL (will use hostname part to resolve IP if `ip` is empty)
url = f'http://{ip}/cam-mid.jpg'
signals_url = f'http://{ip}/signals'

# CSV logging setup
date_str = datetime.now().strftime("%Y%m%d")
csv_filename = os.path.join(base_path, f'{date_str}_DetectionLog.csv')

# Create CSV file with header if not exist
if not os.path.exists(csv_filename):
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time', 'Temperature', 'Humidity'])

def get_sensor_data():
    """Fetch temperature and humidity from ESP32 /signals endpoint"""
    try:
        response = requests.get(signals_url, timeout=5)
        if response.status_code == 200:
            data = response.text.split(',')
            if len(data) == 2:
                temp = float(data[0])
                humidity = float(data[1])
                return temp, humidity
    except Exception as e:
        print(f"Error fetching sensor data: {e}")
    return None, None

def generate_frames():
    cap = cv2.VideoCapture(url)
    while True:
        try:
            success, frame = cap.read()
            if not success or frame is None:
                cap.release()
                cap = cv2.VideoCapture(url)
                continue
            
            # Use current currentTime for filename and CSV log
            currentTime = datetime.now().strftime("%H.%M.%S.%f")
            filename = os.path.join(base_path, f"Frame_{currentTime}.jpg")
            cv2.imwrite(filename, frame)
            
            '''# Also take pictures at specific currentTime of day
            if datetime.now().hour == 17 and datetime.now().minute == 00 and datetime.now().second == 00:
                cv2.imwrite(base_path + f'/Evening_{date_str}_{currentTime}.jpg', frame)'''

            # Log currentTime and sensor data to CSV
            temp, humidity = get_sensor_data()
            with open(csv_filename, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([currentTime, temp, humidity])

            # Encode frame as JPEG (Display in web server)
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()

            # Yield frame bytes for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # Control frame rate
            time.sleep(0.5) # 50 fps

        except Exception as e:
            print(f"Stream generation error: {e}")
            time.sleep(1)

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
    temp, humidity = get_sensor_data()
    return jsonify({
        'temperature': temp,
        'humidity': humidity,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)