# %%
# Libraries
import os
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio as psnr_func
from skimage.metrics import structural_similarity as ssim_func
print('Loaded libraries')

# %%
# Experiment
compressMethods = ['jpg', 'png', 'webp']
user = 'dk1023'
data = 'IISE 2026 Round 1 Data'
experimentDate = '2025-12-30' #2026-1-14
compressQualities = [50, 60, 70, 80, 90] #[10, 15, 20, 25, 30]
print('Loaded experiment parameters')

#%%
# Data Storage Costs
jpeg_sizes = [1.45, 1.50, 1.62, 2.01, 2.64]
webp_sizes = [0.92, 1.01, 1.08, 1.22, 1.61]

x = np.arange(len(compressQualities))  # Label locations
width = 0.35  # Width of bars

fig, ax = plt.subplots(figsize=(8, 4))
bars1 = ax.bar(x - width/2, jpeg_sizes, width, label='JPEG', color='red')
bars2 = ax.bar(x + width/2, webp_sizes, width, label='WebP', color='blue')

# Customize
ax.set_xlabel('Compression Quality (CQ)', fontweight='bold')
ax.set_ylabel('Size (MB)', fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(compressQualities) # type: ignore
ax.legend()

# Add value labels on bars
ax.bar_label(bars1, fmt='%.2f', fontweight='bold')
ax.bar_label(bars2, fmt='%.2f', fontweight='bold')

plt.tight_layout()
plt.show()

# %%
# Collate all time series information
refinedDF_JPEG, refinedDF_WEBP = [], []
for cq in compressQualities:
    # Load time series (JPEG)
    path = f"C:\\Users\\{user}\\Desktop\\{data}\\{experimentDate}_SoftAP_NoBase64_{compressMethods[0]}_{cq}"
    path = f"D:\\{data}\\{experimentDate}_SoftAP_NoBase64_{compressMethods[0]}_{cq}"
    CSV_PATH = os.path.join(path, f"{experimentDate}_timeseries.csv")
    df = pd.read_csv(CSV_PATH)[:60].drop(columns=['counter'])

    # Extract timestamp_ms column and convert to samplingRate
    timestamps_ms = df['timestamp_ms'] / 1000
    samplingRate = []
    for i in range(1, len(timestamps_ms)):
        delta = timestamps_ms[i] - timestamps_ms[i - 1]
        samplingRate.append(delta)

    # Compute latency for samplingRate
    latency = []
    for t in range(len(samplingRate)):
        late = np.abs(samplingRate[t] - 10)
        latency.append(late)
        
    # First entry has no previous timestamp
    samplingRate.insert(0, 0)
    latency.insert(0, 0)
    refinedDF_JPEG.append(pd.DataFrame({'samplingRate': samplingRate, 'latency': latency}))
    
    # Load time series (WEBP)
    path1 = f"C:\\Users\\{user}\\Desktop\\{data}\\{experimentDate}_SoftAP_NoBase64_{compressMethods[2]}_{cq}"
    path1 = f"D:\\{data}\\{experimentDate}_SoftAP_NoBase64_{compressMethods[2]}_{cq}"
    CSV_PATH1 = os.path.join(path1, f"{experimentDate}_timeseries.csv")
    df1 = pd.read_csv(CSV_PATH1)[:60].drop(columns=['counter'])

    # Extract timestamp_ms column and convert to samplingRate1
    timestamps_ms1 = df1['timestamp_ms'] / 1000
    samplingRate1 = []
    for j in range(1, len(timestamps_ms1)):
        delta1 = timestamps_ms1[j] - timestamps_ms1[j - 1]
        samplingRate1.append(delta1)

    # Compute latency for samplingRate1
    latency1 = []
    for k in range(len(samplingRate1)):
        late1 = np.abs(samplingRate1[k] - 10)
        latency1.append(late1)

    # First entry has no previous timestamp
    samplingRate1.insert(0, 0)
    latency1.insert(0, 0)
    refinedDF_WEBP.append(pd.DataFrame({'samplingRate': samplingRate1, 'latency': latency1}))
print('Collated all time series data')

#%%
# Table for time series
tableData = {'Compression Quality (CQ)': compressQualities,
             'JPEG Mean Sampling Rate (s)': [round(df['samplingRate'].mean(), 4) for df in refinedDF_JPEG],
             'JPEG Mean Latency (s)': [round(df['latency'].mean(), 4) for df in refinedDF_JPEG],
             'WEBP Mean Sampling Rate (s)': [round(df['samplingRate'].mean(), 4) for df in refinedDF_WEBP],
             'WEBP Mean Latency (s)': [round(df['latency'].mean(), 4) for df in refinedDF_WEBP]}
tableData = pd.DataFrame(tableData)
print(tableData)

#%%
'''# Line plot JPEG and WEBP combined (2x5 grid)
fig, axes = plt.subplots(2, 5, figsize=(12, 4))
#fig.suptitle('Sampling Rate Variations: JPEG (top) vs WEBP (bottom)', fontsize=16, fontweight='bold')

# JPEG row (top)
for i in range(len(compressQualities)):
    axes[0, i].plot(range(len(refinedDF_JPEG[i])), refinedDF_JPEG[i]['samplingRate'],
                    marker='o', linestyle='-', color='red', linewidth=2)
    axes[0, i].set_title(f"CQ = {compressQualities[i]}: {refinedDF_JPEG[i]['samplingRate'].mean():.2f} ± {refinedDF_JPEG[i]['samplingRate'].std():.2f}",
                         fontweight='bold')
    axes[0, i].grid()

# WEBP row (bottom)
for i in range(len(compressQualities)):
    axes[1, i].plot(range(len(refinedDF_WEBP[i])), refinedDF_WEBP[i]['samplingRate'],
                    marker='o', linestyle='-', color='blue', linewidth=2)
    axes[1, i].set_title(f"CQ = {compressQualities[i]}: {refinedDF_WEBP[i]['samplingRate'].mean():.2f} ± {refinedDF_WEBP[i]['samplingRate'].std():.2f}",
                         fontweight='bold')
    axes[1, i].grid()

# Shared axis labels
fig.supxlabel('Sample Index', fontweight='bold')
fig.supylabel('Collection Rate Between Samples (s)', fontweight='bold')

# Adjust spacing
plt.subplots_adjust(left=0.08, right=0.98, wspace=0.35, hspace=0.4, top=0.90, bottom=0.12)
plt.show()'''

#%%
'''# Single data point
singlePath = f"C:\\Users\\{user}\\Desktop\\{data}\\{experimentDate}_SoftAP_NoBase64_{compressMethods[0]}_{compressQualities[0]}"
print('Loaded single data point path')

# Image files
i = 3
fileCount = []
for file in os.listdir(singlePath + '/Original'):
    if file.endswith('.npy'):
        fileCount.append(file.split('_')[1].split('.')[0])
fileCount = sorted(fileCount, key=lambda x: int(x))[i]

# Individual images
file = np.load(singlePath + '/Original' + f'/img_{fileCount}.npy')
np.save(f"C:\\Users\\{user}\\Desktop\\{data}\\Image {fileCount}.npy", file)'''

#%%
'''# New compression qualities that actually make a difference
#compressQualities = [1, 2, 3, 4, 5]

# Save compressed images with five compression qualities and display in 2x5 grid
output_dir = f"C:\\Users\\{user}\\Desktop\\{data}\\Compressed"
os.makedirs(output_dir, exist_ok=True)

# Convert BGR to RGB if needed (common from OpenCV/some sensors)
file_rgb = file.astype('uint8')
if file_rgb.shape[2] == 3:
    # Assume BGR format, convert to RGB
    file_rgb = file_rgb[..., ::-1]

# Convert numpy array to PIL Image with explicit RGB mode
img_pil = Image.fromarray(file_rgb, mode='RGB')

# Save compressed versions and load for display
compressed_images = {'jpg': [], 'webp': []}

bpp_vals, psnr_vals, ssim_vals = [], [], []
for method in ['jpg', 'webp']:
    for quality in compressQualities:
        save_path = os.path.join(output_dir, f'{method}_q{quality}.{method}')
        
        if method == 'jpg':
            cv2.imwrite(save_path, cv2.cvtColor(file_rgb, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, quality])
        else:  # webp
            cv2.imwrite(save_path, cv2.cvtColor(file_rgb, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_WEBP_QUALITY, quality])
        
        # Load back for display and ensure RGB
        img_loaded = Image.open(save_path).convert('RGB')
        compressed_images[method].append(np.array(img_loaded))
        print(f'Saved and loaded: {method}_q{quality}')
        
        # Log Compression Metrics
        bpp_vals.append(os.path.getsize(save_path) * 8 / (file.shape[0] * file.shape[1] * file.shape[2]))
        psnr_vals.append(psnr_func(file_rgb, np.array(img_loaded)))
        
        # Ensure consistent dtype and data range for SSIM
        file_img = file_rgb.astype(np.float32)
        comp_img = np.array(img_loaded).astype(np.float32)
        data_range = file_img.max() - file_img.min()
        if data_range == 0:
            data_range = 1.0
        try:
            ssim_value = ssim_func(file_img, comp_img, full=True, channel_axis=2, data_range=data_range)[0]
        except TypeError:
            ssim_value = ssim_func(file_img, comp_img, full=True, multichannel=True, data_range=data_range)[0]
        ssim_vals.append(ssim_value)
print('All compressed images saved and loaded')'''

#%%
'''# Create 2x5 grid with color-coded titles
fig, axes = plt.subplots(2, 5, figsize=(12, 6)) # 4 to 6 is the magic number for LaTeX compatibility
# Draw base title in black, then overlay colored words for JPEG and WEBP
#base_title = 'Snapshot of Lee Hall at Various Compression Qualities (Red = JPEG, Blue = WEBP)'
#fig.suptitle(base_title, color='black', fontweight='bold', fontsize=15)

# JPEG row (orange labels)
for col, quality in enumerate(compressQualities):
    axes[0, col].imshow(compressed_images['jpg'][col])
    axes[0, col].set_title(f'CQ = {quality}\nBPP = {bpp_vals[col]:.4f}\nSize = {os.path.getsize(os.path.join(output_dir, f"jpg_q{quality}.jpg"))/ 1024:<.2f} KB', color='red', fontweight='bold')
    axes[0, col].axis('off')

# WEBP row (green labels)
for col, quality in enumerate(compressQualities):
    axes[1, col].imshow(compressed_images['webp'][col])
    axes[1, col].set_title(f'CQ = {quality}\nBPP = {bpp_vals[col + 5]:.4f}\nSize = {os.path.getsize(os.path.join(output_dir, f"webp_q{quality}.webp"))/ 1024:<.2f} KB', color='blue', fontweight='bold')
    axes[1, col].axis('off')

plt.tight_layout()
plt.show()'''

#%%
'''# RD Curve for single image
bpp_jpg = bpp_vals[:5]
bpp_webp = bpp_vals[5:]
psnr_jpg = psnr_vals[:5]
psnr_webp = psnr_vals[5:]
ssim_jpg = [val * 100 for val in ssim_vals[:5]]  # Convert to percentage
ssim_webp = [val * 100 for val in ssim_vals[5:]]  # Convert to percentage

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))
#fig.suptitle('Rate-Distortion Curve of Lee Hall', fontsize=16, fontweight='bold')
fig.supylabel('SSIM (%)', fontweight='bold')

ax1.plot(compressQualities, ssim_jpg, marker='o', label='JPEG', color='red', linewidth=2)
ax1.plot(compressQualities, ssim_webp, marker='o', label='WebP', color='blue', linewidth=2)
ax1.set_xlabel('Compression Quality (CQ)', fontweight='bold')
ax1.legend()
ax1.grid(True)

ax2.plot(bpp_jpg, ssim_jpg, marker='o', label='JPEG', color='red', linewidth=2)
ax2.plot(bpp_webp, ssim_webp, marker='o', label='WebP', color='blue', linewidth=2)
ax2.set_xlabel('Bit-rate (BPP)', fontweight='bold')
ax2.legend()
ax2.grid(True)

# Adjust spacing
plt.subplots_adjust(left=0.08, right=0.98, wspace=0.35, hspace=0.4, top=0.90, bottom=0.12)
plt.show()'''

#%% 
# RD Curve for ALL images 1
# jpg
averageBPP_JPG, averagePSNR_JPG, averageSSIM_JPG = [], [], []
for q in range(len(compressQualities)):
    path = f"C:\\Users\\{user}\\Desktop\\{data}\\{experimentDate}_SoftAP_NoBase64_{compressMethods[0]}_{compressQualities[q]}"
    path = f"D:\\{data}\\{experimentDate}_SoftAP_NoBase64_{compressMethods[0]}_{compressQualities[q]}"

    # Image files
    fileCount = []
    for file in os.listdir(path + '/Original'):
        if file.endswith('.npy'):
            fileCount.append(file.split('_')[1].split('.')[0])
    fileCount = sorted(fileCount, key=lambda x: int(x))[:60]

    # Individual image bpp and PSNRs
    bpps, psnrs, ssims = [], [], []
    for i in fileCount:
        file = np.load(path + '/Original' + f'/img_{i}.npy')
        bpp = os.path.getsize(path + '/jpg' + f'/img_{i}.jpg') * 8 / (file.shape[0] * file.shape[1] * file.shape[2])
        bpps.append(bpp)
        
        compressedFile = np.array(Image.open(path + '/jpg' + f'/img_{i}.jpg'))
        psnr_value = psnr_func(file, compressedFile)
        psnrs.append(psnr_value)

        # Ensure consistent dtype and data range for SSIM
        file_img = file.astype(np.float32)
        comp_img = compressedFile.astype(np.float32)
        data_range = file_img.max() - file_img.min()
        if data_range == 0:
            data_range = 1.0
        try:
            ssim_value = ssim_func(file_img, comp_img, full=True, channel_axis=2, data_range=data_range)[0]
        except TypeError:
            ssim_value = ssim_func(file_img, comp_img, full=True, multichannel=True, data_range=data_range)[0]
        ssims.append(ssim_value)

    # Compute Averages
    averageBPP_JPG.append(sum(bpps) / len(bpps))
    averagePSNR_JPG.append(sum(psnrs) / len(psnrs))
    averageSSIM_JPG.append((sum(ssims) / len(ssims)) * 100)  # Convert to percentage
    print('All image data loaded')

# webp
averageBPP_WEBP, averagePSNR_WEBP, averageSSIM_WEBP = [], [], []
for q in range(len(compressQualities)):
    path = f"C:\\Users\\{user}\\Desktop\\{data}\\{experimentDate}_SoftAP_NoBase64_{compressMethods[2]}_{compressQualities[q]}"
    path = f"D:\\{data}\\{experimentDate}_SoftAP_NoBase64_{compressMethods[2]}_{compressQualities[q]}"

    # Image files
    fileCount = []
    for file in os.listdir(path + '/Original'):
        if file.endswith('.npy'):
            fileCount.append(file.split('_')[1].split('.')[0])
    fileCount = sorted(fileCount, key=lambda x: int(x))[:60]

    # Individual image bpp and PSNRs
    bpps, psnrs, ssims = [], [], []
    for i in fileCount:
        file = np.load(path + '/Original' + f'/img_{i}.npy')
        bpp = os.path.getsize(path + '/webp' + f'/img_{i}.webp') * 8 / (file.shape[0] * file.shape[1] * file.shape[2])
        bpps.append(bpp)
        
        compressedFile = np.array(Image.open(path + '/webp' + f'/img_{i}.webp'))
        psnr_value = psnr_func(file, compressedFile)
        psnrs.append(psnr_value)

        # Ensure consistent dtype and data range for SSIM
        file_img = file.astype(np.float32)
        comp_img = compressedFile.astype(np.float32)
        data_range = file_img.max() - file_img.min()
        if data_range == 0:
            data_range = 1.0
        try:
            ssim_value = ssim_func(file_img, comp_img, full=True, channel_axis=2, data_range=data_range)[0]
        except TypeError:
            ssim_value = ssim_func(file_img, comp_img, full=True, multichannel=True, data_range=data_range)[0]
        ssims.append(ssim_value)

    # Compute Averages
    averageBPP_WEBP.append(sum(bpps) / len(bpps))
    averagePSNR_WEBP.append(sum(psnrs) / len(psnrs))
    averageSSIM_WEBP.append((sum(ssims) / len(ssims)) * 100)  # Convert to percentage
    print('All image data loaded')

#%%
# RD Curve for ALL images 2
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), sharey=True)

# Plot JPEG and WEBP SSIM vs Bit-rate
ax1.plot(averageBPP_JPG, averageSSIM_JPG, marker='o', label='JPEG', color='red', linewidth=2)
ax1.plot(averageBPP_WEBP, averageSSIM_WEBP, marker='o', label='WebP', color='blue', linewidth=2)
ax1.set_xlabel('Bit-rate (BPP)', fontweight='bold')
ax1.legend()
ax1.grid(True)

# Annotate each point with its value
for x, y in zip(averageBPP_JPG, averageSSIM_JPG):
    ax1.annotate(f'{x:.4f}', (x, y), textcoords="offset points", xytext=(0,8), ha='center', fontsize=9, fontweight='bold')
for x, y in zip(averageBPP_WEBP, averageSSIM_WEBP):
    ax1.annotate(f'{x:.4f}', (x, y), textcoords="offset points", xytext=(0,8), ha='center', fontsize=9, fontweight='bold')

# Plot JPEG and WEBP SSIM vs Compression Quality
ax2.plot(compressQualities, averageSSIM_JPG, marker='o', label='JPEG', color='red', linewidth=2)
ax2.plot(compressQualities, averageSSIM_WEBP, marker='o', label='WebP', color='blue', linewidth=2)
ax2.set_xlabel('Compression Quality (CQ)', fontweight='bold')
ax2.legend()
ax2.grid(True)

# Annotate each point with its value
for x, y in zip(compressQualities, averageSSIM_JPG):
    ax2.annotate(f'{y:.2f}', (x, y), textcoords="offset points", xytext=(0,8), ha='center', fontsize=9, fontweight='bold')
for x, y in zip(compressQualities, averageSSIM_WEBP):
    ax2.annotate(f'{y:.2f}', (x, y), textcoords="offset points", xytext=(0,8), ha='center', fontsize=9, fontweight='bold')

fig.supylabel('SSIM (%)', fontweight='bold')
plt.tight_layout()
plt.show()
    
#%%
'''# png
averageBPP_PNG, averagePSNR_PNG = [], []
for q in range(len(compressQualitiesPNG)):
    path = f"C:\\Users\\Ethan\\Downloads\\IISE 2026 Round 1 Data\\{experimentDate}_SoftAP_NoBase64_{compressMethods[1]}_{compressQualitiesPNG[q]}"

    # Image files
    fileCount = []
    for file in os.listdir(path + '/Original'):
        if file.endswith('.npy'):
            fileCount.append(file.split('_')[1].split('.')[0])
    fileCount = sorted(fileCount, key=lambda x: int(x))[:60]

    # Individual image bpp and PSNRs
    bpps, psnrs = [], []
    for i in fileCount:
        file = np.load(path + '/Original' + f'/img_{i}.npy')
        bpp = os.path.getsize(path + '/png' + f'/img_{i}.png') * 8 / (file.shape[0] * file.shape[1] * file.shape[2])
        bpps.append(bpp)
        compressedFile = np.array(Image.open(path + '/png' + f'/img_{i}.png'))
        psnr_value = psnr(file, compressedFile)
        psnrs.append(psnr_value)
        
    # Compute Averages
    averageBPP_PNG.append(sum(bpps) / len(bpps))
    averagePSNR_PNG.append(sum(psnrs) / len(psnrs))
    print('All image data loaded')

# Chosen data point
fc = int(fileCount)
chosenData = pd.read_csv("C:\\Users\\Ethan\\Downloads\\IISE 2026 Round 1 Data\\2025-12-30_SoftAP_NoBase64_jpg_50\\2025-12-30_timeseries.csv")[fc-1:fc]
chosenImage = Image.open("C:\\Users\\Ethan\\Downloads\\IISE 2026 Round 1 Data\\Compressed_Grid\\webp_q50.webp")
print('Loaded chosen data point')

# Display chosen data point
plt.figure(figsize=(6.4, 4.8))
plt.title('Temp: ' + str(chosenData['temp_C'].values[0]) + '°C' +
          ' | Humidity: ' + str(chosenData['humidity_%'].values[0]) + '%' +
          ' | Light: ' + str(chosenData['light_%'].values[0]) + '%', fontweight='bold')
plt.imshow(chosenImage)
plt.axis('off')'''
