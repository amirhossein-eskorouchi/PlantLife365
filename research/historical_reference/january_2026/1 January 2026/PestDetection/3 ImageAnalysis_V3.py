#%%
# Libraries
import os
from PIL import Image
import skimage
import numpy as np
import matplotlib.pyplot as plt
from datetime import date
print('Loaded libraries')

# %%
# Configure settings
date = '2026-01-31'
sample, actualInsects = 2, 181
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
plt.imshow(original)
plt.title(f'Manually Counted Pests: {actualInsects}')

# %%
# Convert to grayscale
grayscale = np.array(original.convert('L'))
plt.imshow(grayscale, cmap='gray')
plt.title('Grayscale Image')

# %%
# Convert to binary with local thresholding
from skimage import filters, measure, morphology
block_size = 255
local_thresh = filters.threshold_local(grayscale, block_size, offset=35)
binary = grayscale < local_thresh

# Label connected components and measure properties
label_img = measure.label(binary)
props = measure.regionprops(label_img)

# Parameters for target size (pixels) and tolerances
if sample == 1:
    target_h, target_w, tol_pixels = 80, 80, 70
elif sample == 2:
    target_h, target_w, tol_pixels = 80, 80, 70
elif sample == 3:
    target_h, target_w, tol_pixels = 100, 50, 20

# Prepare plot: binary image with contours overlaid
fig, ax = plt.subplots(figsize=(8, 8))
ax.imshow(binary, cmap='gray')
found = 0

for prop in props:
    minr, minc, maxr, maxc = prop.bbox
    h = maxr - minr
    w = maxc - minc

    if (abs(h - target_h) <= tol_pixels) and (abs(w - target_w) <= tol_pixels):
        # contour coordinates are relative to the cropped prop.image — offset by bbox origin
        for contour in measure.find_contours(prop.image):
            contour[:, 0] += minr
            contour[:, 1] += minc
            #ax.plot(contour[:, 1], contour[:, 0], linewidth=2, color='red')
            
        rect = plt.Rectangle((minc, minr), w, h, edgecolor='lime', facecolor='none', linewidth=1.5)
        ax.add_patch(rect)
        found += 1

ax.set_title(f"Generated Regions of Interest: {found}")
ax.axis('off')
plt.show()

# %%
