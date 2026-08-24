#%%
# Kernel/Interpreter: objDetect (Interactive Window)
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import skimage
from ultralytics import YOLO
print('Loaded libraries')

# %%
# View image
userName = 'Ethan'
path = f'C:\\Users\\{userName}\\Desktop\\SmartDeltaTrapPhotos\\Photos'
files = [f for f in os.listdir(path) if f.lower().endswith('.jpg')]
print(files)

# %%
# Load model
modelPath = f'C:\\Users\\{userName}\\Desktop\\SmartDeltaTrapPhotos'
model = YOLO(modelPath + "/yolo11x.pt")
print(model)

# %%
# Choose and open image
num = 82
chosenImage = cv2.imread(path + '/' + files[num])

plt.figure(0)
plt.title(f'Image {num}')
plt.imshow(chosenImage)
plt.axis('off')
print('Image size:', chosenImage.shape)

# %%
# Inference
results = model(chosenImage)  # predict on an image

# Access the results
for result in results:
    # Get bounding box coordinates in different formats
    xywh = result.boxes.xywh        # center-x, center-y, width, height
    xywhn = result.boxes.xywhn      # normalized format
    xyxy = result.boxes.xyxy        # top-left-x, top-left-y, bottom-right-x, bottom-right-y
    xyxyn = result.boxes.xyxyn      # normalized corners
    
    # Get class names and confidence scores
    names = [result.names[cls.item()] for cls in result.boxes.cls.int()]  # class name of each box                                       # score of each box

    # Print results
    print('')
    confs = result.boxes.conf
    for i in range(len(names)):
        print("Box:", xyxy[i].tolist(), "Class:", names[i], "Confidence:", confs[i].item())

    # Visualize or save annotated image if needed
    result.show()    # Show results in a window (supported environments)
    
# %%
