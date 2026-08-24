# Import OpenCV for computer vision tasks
import cv2
# Import numpy for numerical operations
import numpy as np
# Import urllib to handle image download from URL
import urllib.request
# Import datetime to handle timestamps
from datetime import datetime

# Set the username for saving images
userName = 'Ethan'
# Set the path where images will be saved
path = f'C:\\Users\\{userName}\\Desktop\\SmartDeltaTrapPhotos'

# URL of the camera image stream
url = 'http://192.168.1.1/cam-hi.jpg'
 
# Initialize video capture from the URL
cap = cv2.VideoCapture(url)
# Set width/height for YOLO input
whT = 320
# Confidence threshold for detections
confThreshold = 0.5
# Non-maximum suppression threshold
nmsThreshold = 0.3
# List to store class names
classNames = []
# Read class names from file
with open(classesfile, 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')
# Get current time (24h format)
now = datetime.now()

# Set up YOLO model configuration and weights
classesfile = path + '/coco.names'
modelConfig = path + '/yolov3.cfg'
modelWeights = path + '/yolov3.weights'
# Load YOLO network
net = cv2.dnn.readNetFromDarknet(modelConfig, modelWeights)
# Set backend to OpenCV
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
# Set computation to CPU
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

# Function to find and draw detected objects on the image
def findObject(outputs, im):
    # Get image shape
    hT, wT, cT = im.shape
    # Lists for bounding boxes, class IDs, and confidences
    bbox = []
    classIds = []
    confs = []
    # Loop through each output layer
    for output in outputs:
        # Loop through each detection
        for det in output:
            # Get class scores
            scores = det[5:]
            # Get class with highest score
            classId = np.argmax(scores)
            # Get confidence of the best class
            confidence = scores[classId]
            # Filter out weak predictions
            if confidence > confThreshold:
                # Calculate bounding box coordinates
                w, h = int(det[2] * wT), int(det[3] * hT)
                x, y = int((det[0] * wT) - w / 2), int((det[1] * hT) - h / 2)
                bbox.append([x, y, w, h])
                classIds.append(classId)
                confs.append(float(confidence))
    # Apply non-maximum suppression to remove overlapping boxes
    indices = cv2.dnn.NMSBoxes(bbox, confs, confThreshold, nmsThreshold)
    
    # Draw bounding boxes and labels for each detection
    personCount, plantCount = 0, 0
    for i in indices:
        box = bbox[i]
        x, y, w, h = box[0], box[1], box[2], box[3]
        # Draw rectangle around detected object
        cv2.rectangle(im, (x, y), (x + w, y + h), (255, 0, 255), 2)
        # Put class name and confidence on the image
        cv2.putText(im, f'{classNames[classIds[i]].upper()} {int(confs[i] * 100)}%', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
        
        # Uncomment below to save image if person detected
        if classNames[classIds[i]] == 'person':
            personCount += 1
            
        elif classNames[classIds[i]] == 'pottedplant':
            plantCount += 1
        
        print(f'Person(s): {personCount} | Plant(s): {plantCount}')
            
    '''if (past == fut):
        currentTime = now.strftime(f"%Y%m%d - %H.%M.%S")
        cv2.imwrite(path + f'/{currentTime}_{indices}.jpg', im)
        fut = past'''
       
# Main loop for real-time detection
while True:
    # Download image from camera URL
    img_resp = urllib.request.urlopen(url)
    # Convert image bytes to numpy array
    imgnp = np.array(bytearray(img_resp.read()), dtype=np.uint8)
    # Decode image
    im = cv2.imdecode(imgnp, -1)
    # Read frame from video capture (not used)
    sucess, img = cap.read()
    # Create blob from image for YOLO
    blob = cv2.dnn.blobFromImage(im, 1/255, (whT, whT), [0, 0, 0], 1, crop=False)
    # Set input to the network
    net.setInput(blob)
    # Get output layer names
    layernames = net.getLayerNames()
    outputNames = [layernames[i-1] for i in net.getUnconnectedOutLayers()]
    # Run forward pass
    outputs = net.forward(outputNames)
    # Find and draw objects
    findObject(outputs, im)
    # Show the image
    cv2.imshow('Image', im)
    # Wait for key press
    key = cv2.waitKey(5)
    # Save image if 's' key is pressed
    if key == ord('s'):
        currentTime = now.strftime(f"%Y%m%d - %H.%M.%S")
        cv2.imwrite(path + f'/{currentTime}.jpg', im)
    # Exit loop if 'q' key is pressed
    if key == ord('q'):
        break