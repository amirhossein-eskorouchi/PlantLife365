# Import library (NO JUPYTER NOTEBOOK, just Run Python File on VSCode)
import cv2
import numpy as np
import urllib.request
from datetime import datetime

# Save location for images
userName = 'Ethan'
path = f'C:\\Users\\{userName}\\Desktop\\SmartDeltaTrapPhotos'
 
# Replace the URL with the IP camera's stream URL
url = 'http://192.168.0.252/cam-hi.jpg'
cv2.namedWindow("Live Cam Testing", cv2.WINDOW_AUTOSIZE)

# Create a VideoCapture object
cap = cv2.VideoCapture(url)
 
# Check if the IP camera stream is opened successfully
if not cap.isOpened():
    print("Failed to open the IP camera stream")
    exit()
 
# Read and display video frames
while True:
    # Read a frame from the video stream
    img_resp = urllib.request.urlopen(url)
    imgnp = np.array(bytearray(img_resp.read()),dtype=np.uint8)
    image = cv2.imdecode(imgnp,-1)
    
    # Load the window that views image
    cv2.imshow('Live Cam Testing', image)
    key = cv2.waitKey(5)
    
    # In 24h time
    now = datetime.now()
    
    # Take image at a certain time of day
    if now.hour == 16 and now.minute == 00 and now.second == 00:
        currentTime = now.strftime(f"%Y%m%d - %H.%M.%S")
        cv2.imwrite(path + f'/{currentTime}.jpg', image)
    
    # Regular image snap
    if key == ord('s'):
        currentTime = now.strftime(f"%Y%m%d - %H.%M.%S")
        cv2.imwrite(path + f'/{currentTime}.jpg', image)
    
    # Stop running code
    if key == ord('q'):
        break
    
cap.release()
cv2.destroyAllWindows()