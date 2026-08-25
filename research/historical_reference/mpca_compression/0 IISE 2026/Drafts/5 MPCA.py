#%%
# Libraries
import os
import numpy as np
import torch
import time
import matplotlib.pyplot as plt
from PIL import Image
import cv2
from sklearn.metrics import mean_squared_error as mse
from skimage.metrics import peak_signal_noise_ratio as psnr
from joblib import dump, load
print(torch.cuda.is_available())
print('Loaded all libraries')

#%% 
# 1. Experimental setup
#trainPath = 'PROJECT_ROOT/Photos'
trainPath = 'PROJECT_ROOT/Data'

save = trainPath + '/1 Original RGB Data'
compSave = trainPath + '/2 Compressed RGB Data'
recSave = trainPath + '/3 Reconstructed RGB Data'
modelSave = trainPath + '/4 Compression Models'

# Load file names
trainNames = [f for f in os.listdir(trainPath) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
print(len(trainNames), 'validation images')

device = 'cpu'

#%%
# View train image
idx = 0
img_path = trainPath + '/' + trainNames[idx]
img = np.array(Image.open(img_path))
print(f"Loaded image shape: {img.shape}, dtype: {img.dtype}")

# Ensure image is 3D (add channel dimension if grayscale)
if img.ndim == 2:
    img = np.expand_dims(img, axis=-1)
    print(f"Converted grayscale to 3D: {img.shape}")

plt.imshow(img if img.shape[-1] == 3 else img[:, :, 0], cmap='gray' if img.shape[-1] == 1 else None)
plt.title(f"Image shape: {img.shape}")
plt.show()

# Ensure save directory exists
os.makedirs(save, exist_ok=True)

# OpenCV expects BGR ordering — convert from PIL/NumPy RGB to BGR before writing
to_save = img
if img.ndim == 3 and img.shape[2] == 3:
    # convert RGB -> BGR
    to_save = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

cv2.imwrite(os.path.join(save, f"Original Image {trainNames[idx]}"), to_save)
print('JPEG file size:', os.path.getsize(img_path))

#%%
def MPCA_RGB_compress(X, n_row_components, n_col_components, n_channel_components, 
                      cameraMin=0, cameraMax=255, device=device):
    if not isinstance(X, torch.Tensor):
        X = torch.tensor(X, dtype=torch.uint8, device=device)
    else:
        X = X.to(device).float()

    H, W, C = X.shape
    X_scaled = (X - cameraMin) / (cameraMax - cameraMin)
    mean_X = torch.mean(X_scaled, dim=(0, 1), keepdim=True)
    X_centered = X_scaled - mean_X

    projection_matrices = {}

    # Parallel SVD computations
    row_task = torch.jit.fork(lambda: torch.linalg.svd(X_centered.reshape(H, -1), full_matrices=False))
    col_task = torch.jit.fork(lambda: torch.linalg.svd(X_centered.permute(1, 0, 2).reshape(W, -1), full_matrices=False))
    chan_task = torch.jit.fork(lambda: torch.linalg.svd(X_centered.permute(2, 0, 1).reshape(C, -1), full_matrices=False))

    U1 = torch.jit.wait(row_task)[0]
    U2 = torch.jit.wait(col_task)[0]
    U3 = torch.jit.wait(chan_task)[0]

    P = min(n_row_components, H)
    Q = min(n_col_components, W)
    R = min(n_channel_components, C)

    projection_matrices['row'] = U1[:, :P]
    projection_matrices['col'] = U2[:, :Q]
    projection_matrices['channel'] = U3[:, :R]

    # Apply projections
    Y = torch.einsum('pi,ijk->pjk', U1[:, :P].t(), X_centered)
    Y = torch.einsum('qj,pjk->pqk', U2[:, :Q].t(), Y)
    Y = torch.einsum('cr,pqc->pqr', U3[:, :R].t(), Y)

    # Uniform quantization (global whole-tensor)
    '''if quantize_levels and int(quantize_levels) > 1 and torch.is_floating_point(Y):
        levels = int(quantize_levels)
        Y_min = float(torch.min(Y).item())
        Y_max = float(torch.max(Y).item())
        # avoid zero range
        if Y_max == Y_min:
            Y_max = Y_min + 1e-6
        # quantize to 0..levels-1 and store as uint8 when possible
        Yq = torch.round((Y - Y_min) / (Y_max - Y_min) * (levels - 1)).to(torch.uint8)
        projection_matrices['_quant'] = {'min': Y_min, 'max': Y_max, 'levels': levels, 'dtype': 'uint8'}
    else:
        Yq = Y'''

    return Y, projection_matrices, mean_X.squeeze(0).squeeze(0)

def MPCA_RGB_decompress(Y, projection_matrices, mean_X, 
                        cameraMin=0, cameraMax=255, device=device, apply_dequant=True):
    # Move tensors in dictionaries to the device (skip the internal quant params)
    for key in list(projection_matrices.keys()):
        if key == '_quant':
            continue
        projection_matrices[key] = projection_matrices[key].to(device)

    # Ensure Y is a torch tensor on the correct device
    if isinstance(Y, np.ndarray):
        Y = torch.from_numpy(Y).to(device)
    else:
        Y = torch.tensor(Y, device=device)

    # If Y was quantized (and quant params were stored), optionally dequantize back to float
    if isinstance(projection_matrices, dict) and '_quant' in projection_matrices and apply_dequant:
        q = projection_matrices['_quant']
        levels = int(q['levels'])
        Y = Y.float()
        # dequantize from 0..levels-1 to original range
        Y = (Y / (levels - 1)) * (q['max'] - q['min']) + q['min']
    else:
        # If not dequantizing, just work with the integer codes as floats (lossy reconstruction)
        # Entropy model goes here
        Y = Y.float()

    # Launch asynchronous tasks for inverse projections
    # Project back from channel mode
    task_chan = torch.jit.fork(lambda: torch.einsum('cr,pqc->pqr', projection_matrices['channel'], Y))
    # Wait to get result of channel projection (needed for column mode)
    X_after_chan = torch.jit.wait(task_chan)

    # Project back from column mode
    task_col = torch.jit.fork(lambda: torch.einsum('jq,pqr->pjr', projection_matrices['col'], X_after_chan))
    X_after_col = torch.jit.wait(task_col)

    # Finally, project back from row mode
    task_row = torch.jit.fork(lambda: torch.einsum('hp,pjr->hjr', projection_matrices['row'], X_after_col))
    X_rec = torch.jit.wait(task_row)

    mean_X = mean_X.to(device)
    X_rec = X_rec.permute(0, 1, 2) + mean_X

    X_rec = (cameraMax - cameraMin) * X_rec + cameraMin
    X_rec = torch.clamp(X_rec, cameraMin, cameraMax).to(torch.uint8)

    return X_rec

print('Loaded functions')

#%% 
# Chosen number of PCs (based on bpp)
bpp = 0.1
pc = int(np.sqrt((bpp * img.shape[0] * img.shape[1]) / 32)) # Value = 32 w/o uniform quantization; Value = 8 with uniform quantization
print('Principal components based on BPP:', pc)

#%%
# MPCA compression performance
start = time.time()
compressed = MPCA_RGB_compress(X=img, n_row_components=pc, n_col_components=pc, n_channel_components=pc, 
                               cameraMin=0, cameraMax=255, device=device)[0]
end = time.time()

elapsedMillisecondsMPCA = (end - start) * 1000
elapsedSecondsMPCA = end - start
elapsedMinutesMPCA = elapsedSecondsMPCA / 60

print(f'Elapsed compression time for Test Image at {pc} PCs: {elapsedMillisecondsMPCA:.4f} milliseconds')
print(f'Elapsed compression time for Test Image at {pc} PCs: {elapsedSecondsMPCA:.4f} seconds')
print(f'Elapsed compression time for Test Image at {pc} PCs: {elapsedMinutesMPCA:.4f} minutes')
print('Compressed tensor size:', compressed.shape)

np.save(compSave + f"/Compressed_MPCA_{bpp}BPP_{pc}PCs_{trainNames[idx].split('.jpg')[0]}.npy", compressed.cpu()) # compressed data is bigger w/o uniform quantization
print('JPEG + MPCA file size:', os.path.getsize(compSave + f"/Compressed_MPCA_{bpp}BPP_{pc}PCs_{trainNames[idx].split('.jpg')[0]}.npy"))

#%%
# Store model for later decompression
projectionMatrices = MPCA_RGB_compress(X=img, n_row_components=pc, n_col_components=pc, n_channel_components=pc, 
                                       cameraMin=0, cameraMax=255, device=device)[1] # 256 for 8-bit uniform quantization
mean = MPCA_RGB_compress(X=img, n_row_components=pc, n_col_components=pc, n_channel_components=pc, 
                        cameraMin=0, cameraMax=255, device=device)[2]

dump((projectionMatrices, mean), modelSave + f"/MPCA_{bpp}BPP_{pc}PCs_{trainNames[idx].split('.jpg')[0]}.joblib")

print('Model parameters stored for later decompression')

#%% 
# MPCA decompression performance
originalImage = img
compressedImage = np.load(compSave + f"/Compressed_MPCA_{bpp}BPP_{pc}PCs_{trainNames[idx].split('.jpg')[0]}.npy")
compressedInfo1, compressedInfo2 = load(modelSave + f"/MPCA_{bpp}BPP_{pc}PCs_{trainNames[idx].split('.jpg')[0]}.joblib")

start = time.time()
recMPCA = MPCA_RGB_decompress(Y=compressedImage, projection_matrices=compressedInfo1, mean_X=compressedInfo2, 
                              cameraMin=0, cameraMax=255, apply_dequant=False)
end = time.time()

elapsedMillisecondsMPCA = (end - start) * 1000
elapsedSecondsMPCA = end - start
elapsedMinutesMPCA = elapsedSecondsMPCA / 60

print(f'Elapsed decompression time for Test Image at {pc} PCs: {elapsedMillisecondsMPCA:.4f} milliseconds')
print(f'Elapsed decompression time for Test Image at {pc} PCs: {elapsedSecondsMPCA:.4f} seconds')
print(f'Elapsed decompression time for Test Image at {pc} PCs: {elapsedMinutesMPCA:.4f} minutes')
print('Reconstructed image size:', recMPCA.shape)

#np.save(recSave + f"/Reconstructed_MPCA_{bpp}BPP_{pc}PCs_{trainNames[idx].split('.jpg')[0]}.npy", recMPCA.cpu())
finalRecMPCA = recMPCA.cpu().numpy()

# Ensure output directory exists
os.makedirs(recSave, exist_ok=True)

# Ensure dtype is uint8 for OpenCV
if finalRecMPCA.dtype != 'uint8':
    finalRecMPCA = finalRecMPCA.astype('uint8')

# OpenCV expects BGR channel order; convert from RGB if needed
to_write = finalRecMPCA
if finalRecMPCA.ndim == 3 and finalRecMPCA.shape[2] == 3:
    to_write = cv2.cvtColor(finalRecMPCA, cv2.COLOR_RGB2BGR)

out_path = os.path.join(recSave, f"Reconstructed_MPCA_{bpp}BPP_{pc}PCs_{trainNames[idx]}")
cv2.imwrite(out_path, to_write)
print('JPEG + MPCA file size:', os.path.getsize(out_path))

#%%
# MPCA performance for one image
originalSample = Image.open(img_path)
compressedSample = compressedImage
reconstructedSample = Image.open(recSave + f"/Reconstructed_MPCA_{bpp}BPP_{pc}PCs_{trainNames[idx]}")

residuals = np.array(originalSample) - np.array(reconstructedSample)

fig, axes = plt.subplots(1, 3, figsize=(10, 10))
images = [originalSample, reconstructedSample, residuals]

titles = [
    f'Original Image\nMax Value: {np.max(originalSample):.3f}',
    f'Rec. Image with MPCA\nMax Value: {np.max(reconstructedSample):.3f}',
    f'Residual Image with MPCA\nMin/Max Value: {np.min(residuals):.3f}/{np.max(residuals):.3f}'
]

for ax, image, title in zip(axes.flatten(), images, titles):
    im = ax.imshow(image, cmap='jet')
    ax.set_title(title)
    ax.axis('off')
    fig.colorbar(im, ax=ax, orientation='vertical', fraction=0.046, pad=0.04)  # Adjust these for colorbar size/space

plt.tight_layout()
plt.show()

print("Model size: " + str(os.path.getsize(modelSave + f"/MPCA_{bpp}BPP_{pc}PCs_{trainNames[idx].split('.jpg')[0]}.joblib")) + " bytes")
print(f'File size reduction: {((os.path.getsize(img_path)*8 - compressedSample.nbytes*8) / (os.path.getsize(img_path)*8)) * 100:.3f}%')
print(f'Bit-rate: {compressedSample.nbytes*8 / np.prod(img.shape):.3f} bpp')
print(f'PSNR: {psnr(np.array(originalSample), np.array(reconstructedSample), data_range=255):.3f} dB')
print(f'MSE: {mse(np.array(originalSample).flatten(), np.array(reconstructedSample).flatten()):.3f}')

# %%
# Running into problems with global uniform quantization