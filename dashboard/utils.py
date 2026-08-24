try:
    import serial
except ImportError:
    serial = None
    print("Warning: pyserial not installed. Serial communication will not work.")

import json
import os
import time

try:
    import cv2
except ImportError:
    cv2 = None
    print("Warning: opencv-python not installed. Camera will not work.")

SERIAL_PORT = os.environ.get('PLANTLIFE365_SERIAL_PORT', '/dev/ttyCH341USB0') # this is the default port for the CH340 USB-serial adapter on linux. It may be different on other systems
BAUD_RATE = 9600

def get_sensor_reading():
    """ Connects to the usb cable, reads one line of data and returns as python dictionary"""


    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout =1) as ser: # type: ignore
            ser.reset_input_buffer()
            line = ser.readline().decode('utf-8').strip()
            print("[USB_DATA] Received: {line}")

            if not line:
                return None
            
            try:
                data = json.loads(line)
                data['status'] = 'online'
                return data
            except json.JSONDecodeError:
                parts = line.split(',')
                if len(parts) >= 2:
                    return {
                        'temperature': float(parts[0]),
                        'humidity' : float(parts[1]),
                        'light': float(parts[2]),
                        'water_level': float(parts[3]),
                        'gas': float(parts[4]),
                        'status': 'online',

                    }
                else:
                    print(f"[USB ERROR] Data not in expected format: {line}")
                    return None
                    
    except serial.SerialException: # type: ignore
        print(f"[USB ERROR] Could not find {SERIAL_PORT}.Is the cable plugged in?")
        return {
            'temperature': 0,
            'humidity' : 0,
            'light': 0,
            'water_level': 0,
            'gas': 0,
            'status': 'offline',
        }
    except Exception as e: 
        print(f"[SYSTEM ERROR] {e}")
        return None

ESP_IP = os.environ.get("PLANTLIFE365_ESP_IP", "192.168.4.1")
STREAM_URL = f"http://{ESP_IP}/cam-mid.jpg"
DATA_URL = f"http://{ESP_IP}/signals"

def get_camera_frame():
    """
    This function constantly captures images from the ESP32
      and turns them into a format the browser can display
    """
    cap = cv2.VideoCapture(STREAM_URL) # STREAM_URL # type: ignore

    #if we can't connect to the camera, print an error message but don't crash
    if not cap.isOpened():
        print("Error: Could not connect to ESP32 camera stream at {STREAM_URL}")
        return 
    
    while True:
        try:

            success, frame = cap.read()
            if not success:
                #if the stream drops, wait a bit and try to reconnect
                cap.release()
                time.sleep(1)
                cap = cv2.VideoCapture(STREAM_URL) # type: ignore
                continue

            # convert the raw image to JPEG format
            ret, buffer = cv2.imencode('.jpg', frame) # type: ignore
            if not ret: 
                continue

            frame_bytes = buffer.tobytes()

            # yield the frame in a format that creates a "video" stream 
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # control framerate (wait 0.1 sec)
            time.sleep(0.5)
        
        except Exception as e:
            print(f"Error capturing frame: {e}")
            time.sleep(1)
