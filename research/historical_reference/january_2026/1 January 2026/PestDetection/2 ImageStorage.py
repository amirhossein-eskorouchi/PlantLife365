# Libraries
from flask import Flask, request, jsonify
import os
import json
import numpy as np
import cv2
from datetime import date
from glob import glob

# Configuration
COMPRESS_METHODS = ['jpg', 'png']
ALG = COMPRESS_METHODS[0]
COMPRESS_QUALITY = 100

# Data directory
sample = 'Beta'
DIR = f"{date.today()}_{ALG}{COMPRESS_QUALITY}_Sample {sample}"
os.makedirs(DIR, exist_ok=True)

# In-memory counter
counter = 0

def get_next_counter():
    """Get next unique counter."""
    global counter
    counter += 1
    return counter

def save_image(img, counter_num, alg, quality):
    """Save image to directory."""
    ext = '.jpg' if alg == 'jpg' else '.png'
    filename = f"img_{counter_num:06d}{ext}"
    img_path = os.path.join(DIR, filename)
    
    if alg == 'jpg':
        success = cv2.imwrite(img_path, img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    elif alg == 'png':
        success = cv2.imwrite(img_path, img, [cv2.IMWRITE_PNG_COMPRESSION, quality])
    
    print(f"SAVED [{counter_num:06d}]: {filename} ({img.shape})")
    return success

# Flask app
app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    global counter
    try:
        data_str = request.form.get('data', '{}')
        data = json.loads(data_str)
        print(f"Received: {data.get('image_size', 0)} bytes")
        
        img_file = request.files.get('image')
        if img_file:
            img_array = np.frombuffer(img_file.read(), np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if img is not None:
                next_counter = get_next_counter()
                if save_image(img, next_counter, ALG, COMPRESS_QUALITY):
                    return jsonify({"status": "ok", "counter": next_counter})
                return jsonify({"status": "save_error"}), 500
            print("Decode failed")
        print("No image")
        return jsonify({"status": "ok"})
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error"}), 400

@app.route('/status')
def status():
    img_count = len(glob(os.path.join(DIR, f"img_*{'.' + ALG}")))
    return jsonify({
        "total_images": img_count,
        "directory": DIR
    })

if __name__ == '__main__':
    print(f"Saving to: {DIR}")
    print("ESP32 → 192.168.4.2:5000")
    print("Status: http://192.168.4.2:5000/status")
    app.run(host='0.0.0.0', port=5000, debug=False)