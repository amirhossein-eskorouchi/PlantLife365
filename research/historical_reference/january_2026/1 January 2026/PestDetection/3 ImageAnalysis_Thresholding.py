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
# Load image
ALG = 'jpg'
COMPRESS_QUALITY = '100'
sample = '2'

DIR = f"{date.today()}_{ALG}{COMPRESS_QUALITY}_Sample {sample}"
path = os.listdir(DIR)
print(path)

# %%
# Select image to view
image = path[-1]
original = Image.open(DIR + '/' + image)
plt.imshow(original)
plt.title('Manually Counted Pests: 181')
plt.axis('off')

#%%
import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from skimage import filters

# Assuming 'original' is your PIL Image
# Convert from original to grayscale
grayscale = np.array(original.convert('L'))

# Convert from grayscale to binary (LOCAL THRESHOLDING)
block_size = 29
local_thresh = filters.threshold_local(grayscale, block_size, offset=10)
binary = grayscale < local_thresh

# FIX 1: Convert boolean to uint8 (0/255) for OpenCV
img = (binary * 255).astype(np.uint8)

plt.imshow(binary, cmap='gray')
plt.title('Local thresholding')
plt.axis('off')
plt.show()

# Clean up: remove noise and separate spots
kernel = np.ones((3,3), np.uint8)
cleaned = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)

# Optional: Canny edges for sharper boundaries
edges = cv2.Canny(cleaned, 30, 100)

# Find contours (use cleaned directly)
contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Filter and count by area
min_area, max_area = 10, 200  # Tune these
spots = [c for c in contours if min_area < cv2.contourArea(c) < max_area]
count = len(spots)

print(f"Number of white spots: {count}")

# FIX 2: Create proper 3-channel display image from uint8 cleaned
output = cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR)

# Draw bounding boxes (green)
for c in spots:
    x, y, w, h = cv2.boundingRect(c)
    cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)

# FIX 3: Use matplotlib for better display (handles uint8 properly)
plt.imshow(cv2.cvtColor(output, cv2.COLOR_BGR2RGB))
plt.title(f'Detected Pests via Image Processing Techniques: {count}')
plt.axis('off')
plt.tight_layout()
plt.show()

# %%
