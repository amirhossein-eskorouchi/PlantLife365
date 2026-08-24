import camera
import time
import os

# -------- CONFIG --------
SAMPLE_INTERVAL = 2      # Seconds between photos
IMAGE_PREFIX = "/img_"   # Stored in internal flash

# -------- CAMERA ONLY --------
print("Initializing camera...")
try:
    camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
    print("Camera OK")
except Exception as e:
    print("Camera init FAILED:", e)
    raise SystemExit("Camera not available")

# -------- OPTIONAL: CLEAN OLD IMAGES --------
try:
    for fname in os.listdir("/"):
        if fname.startswith("img_") and fname.endswith(".jpg"):
            os.remove("/" + fname)
    print("Cleared old images")
except:
    pass

# -------- MAIN LOOP: IMAGES ONLY --------
counter = 1
print("Starting image capture loop...")

while True:
    print("Capture", counter)
    try:
        buf = camera.capture()
        if buf:
            img_path = "%s%d.jpg" % (IMAGE_PREFIX, counter)
            with open(img_path, "wb") as f:
                f.write(buf)
            print("Saved", img_path)
            counter += 1
        else:
            print("Empty capture")
    except Exception as e:
        print("Capture FAILED:", e)

    time.sleep(SAMPLE_INTERVAL)
