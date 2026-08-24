# Libraries
from flask import Flask, request, jsonify
import os, csv, base64, numpy as np, cv2
from datetime import date
from PIL import Image

# Configurable compression settings
COMPRESS_METHODS = ['jpg', 'png', 'webp']
ALG = COMPRESS_METHODS[0]
COMPRESS_QUALITY = 50

DIR = f'{date.today()}_SoftAP_Base64_{ALG}_{COMPRESS_QUALITY}'
CSV_PATH = os.path.join(DIR, f'{date.today()}_timeseries.csv')
os.makedirs(DIR, exist_ok=True)

# CSV setup - add compression method column
file_exists = os.path.exists(CSV_PATH)
csv_file = open(CSV_PATH, 'a', newline='')
writer = csv.writer(csv_file)
if not file_exists:
    writer.writerow(['counter', 'timestamp_ms', 'temp_c', 'humidity_pct', 'light_raw'])

app = Flask(__name__)

def save_image(img, counter, alg, quality):
    """Save image with specified compression algorithm"""
    ext = {'jpg':'jpg', 'png':'png', 'webp':'webp'}[alg]
    filename = f"img_{counter}.{ext}"
    filepath = os.path.join(DIR, filename)
    
    if alg == 'jpg':
        cv2.imwrite(filepath, img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    elif alg == 'png':
        cv2.imwrite(filepath, img, [cv2.IMWRITE_PNG_COMPRESSION, quality])
    elif alg == 'webp':
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        pil_img.save(filepath, 'WEBP', quality=quality)
    
    print(f"✓ SAVED: {filename} ({alg}, Q={quality})")
    return True

@app.route('/upload', methods=['POST'])
def upload():
    try:
        data = request.get_json()
        counter = int(data['counter'])
        timestamp = int(data['timestamp'])
        temp = float(data['temp'])
        humidity = float(data['humidity'])
        light = float(data['light'])
        image_size = int(data['image_size'])
        image_b64 = data.get('image_base64')

        print(f"✓ DATA #{counter}: {temp}°C {humidity}% light={light} imgsize={image_size}")

        if image_b64:
            img_bytes = base64.b64decode(image_b64)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is not None:
                save_image(img, counter, ALG, COMPRESS_QUALITY)
            else:
                print("✗ Failed to decode image")

        # Log with compression info
        writer.writerow([counter, timestamp, temp, humidity, light])
        csv_file.flush()
        return jsonify({"status": "ok", "alg": ALG, "quality": COMPRESS_QUALITY})
        
    except Exception as e:
        print("✗ Error:", e)
        return jsonify({"status": "error"}), 400

if __name__ == '__main__':
    print(f"🚀 Server on http://0.0.0.0:5000 (ALG={ALG}, Q={COMPRESS_QUALITY})")
    print("Connect PC to ESP32 WiFi first! Change ALG index above to test formats.")
    app.run(host="0.0.0.0", port=5000, debug=False)