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
plt.imshow(chosenImage, cmap='jet')
plt.axis('off')
plt.colorbar()
print('Image size:', chosenImage.shape)

#%%
# Grayscaled image
grayscaled = cv2.cvtColor(chosenImage, cv2.COLOR_BGR2GRAY)

plt.figure(1)
plt.title('Grayscaled Image')
plt.imshow(grayscaled, cmap='gray')
plt.axis('off')
plt.colorbar()
print('Image size:', grayscaled.shape)

# %%
# Segmented images with Sobel Method
edges = skimage.filters.sobel(grayscaled)

plt.figure(2)
plt.title('Sobel Edges')
plt.imshow(edges, cmap='jet')
plt.colorbar()
plt.axis('off')

#%%
# Threshold edges to get binary image
binary = edges > 0.0175  # You can adjust threshold

plt.figure(3)
plt.title('Binary applied after Sobel Edges')
plt.imshow(binary, cmap='jet')
plt.colorbar()
plt.axis('off')

#%%
# Optional: clean small artifacts
cleaned = skimage.morphology.remove_small_objects(binary, min_size=150)

plt.figure(4)
plt.title('Cleaned image after binary')
plt.imshow(cleaned, cmap='jet')
plt.colorbar()
plt.axis('off')

# %%
