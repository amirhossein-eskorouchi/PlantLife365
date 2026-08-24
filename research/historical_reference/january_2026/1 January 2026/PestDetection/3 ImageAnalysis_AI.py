#%%
# Libraries
import os
import cv2
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from datetime import date
print('Loaded libraries')

# %%
# Configure settings
date = '2026-01-31'
sample = '2'
ALG = 'jpg'
COMPRESS_QUALITY = '100'
print(f'Sample {sample}')

#%%
# Load image directory
DIR = f"{date}_{ALG}{COMPRESS_QUALITY}_Sample {sample}"
path = os.listdir(DIR)
print(path)

# %%
# Select image to view
image = path[-1]
original = Image.open(DIR + '/' + image)
plt.imshow(original, cmap='gray')
plt.title('Original Image')
plt.axis('off')
plt.show()

#%%
# Convert to grayscale
grayscale = np.array(original.convert('L'))
plt.imshow(grayscale, cmap='gray')
plt.title('Grayscale Image')
plt.axis('off')
plt.show()

#%%
# Convert to binary (LOCAL THRESHOLDING)
from skimage import filters
block_size = 99
local_thresh = filters.threshold_local(grayscale, block_size, offset=10)
binary = grayscale < local_thresh
binary = (binary * 255).astype(np.uint8)

plt.imshow(binary, cmap='gray')
plt.title('Local Thresholding')
plt.axis('off')
plt.show()

# %%
# Load Segmentation model and run inference
from ultralytics import FastSAM, SAM, YOLO
model = SAM(r"Models/mobile_sam.pt")
results = model(binary, device="cpu", retina_masks=True)
print('Model inference complete')

#%%
# Assuming everything_results already exists
for i, result in enumerate(results):
    masks_xy = result.masks.xy
    masks_xyn = result.masks.xyn
    masks_tensor = result.masks.data

    print(f"Result {i}: {len(masks_xy)} masks")

    # Plot with boxes only, no labels, no masks
    segmented = result.plot(
        boxes=True,    # draw bounding boxes
        masks=False,   # disable masks overlay
        probs=False,   # disable classification probabilities
        labels=False   # disable text labels (class names, scores)
    )

    # Show with OpenCV (or use matplotlib if you prefer)
    cv2.imshow(f"Result", segmented)
    cv2.waitKey(0)

cv2.destroyAllWindows()

# %%