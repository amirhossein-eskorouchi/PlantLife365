#%%
# Kernel/Interpreter: objDetect (Interactive Window)
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import skimage
print('Loaded libraries')

# %%
# View image
userName = 'Ethan'
path = f'C:\\Users\\{userName}\\Desktop\\SmartDeltaTrapPhotos'
files = os.listdir(path)
print(files)

#%%
# Choose and open image
chosenImage = cv2.imread(path + '/' + files[0])

plt.figure(0)
plt.title('Original Image')
plt.imshow(chosenImage, cmap='viridis')
plt.axis('off')
plt.colorbar()
print('Image size:', chosenImage.shape)

# %%
# Alternative: YOLO
from ultralytics import YOLO
model = YOLO("yolo11n.pt")
print(model)

# %%
# Create a single dataset YAML containing train/valid/test
'''import yaml
dataset = {
    'train': path + '/train',
    'val': path + '/val',
    'test': path + '/test',
    'names': {0:'gray', 1:'lightgray', 2:'yellow', 3:'orange', 4:'black'}}
with open('Dataset' + '/moths.yaml', 'w') as file:
    yaml.dump(dataset, file, default_flow_style=False)
print("Created dataset")'''

#%%
# Train custom dataset
model.train(data='coco128.yaml', epochs=50, imgsz=600)
# Example:
#Class     Images  Instances      Box(P          R      mAP50  mAP50-95)
#person         61        254      0.894      0.709      0.844      0.647

#%%
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
    names = [result.names[cls.item()] for cls in result.boxes.cls.int()]  # class name of each box
    confs = result.boxes.conf                                         # score of each box

    # Print results
    for i in range(len(names)):
        print("Box:", xyxy[i].tolist(), "Class:", names[i], "Confidence:", confs[i].item())

    # Visualize or save annotated image if needed
    result.show()    # Show results in a window (supported environments)
    result.save(filename="AmirDeskExample.jpg")   # Save annotated results

# %%
