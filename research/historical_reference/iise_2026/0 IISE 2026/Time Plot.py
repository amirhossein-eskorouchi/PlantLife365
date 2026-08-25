#%%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

base_path = "PROJECT_ROOT/Data"
fn = base_path + '/20251211_DetectionLog.csv'

df = pd.read_csv(fn)
print("Loaded:", fn, "shape:", df.shape)

#%% 
# Raw sample
print("sample first-col values:", df.iloc[:10, 0].tolist())

#%% 
# Attempt 1: numeric
time_numeric = pd.to_numeric(df.iloc[:, 0], errors='coerce')
num_nonnull = time_numeric.notna().sum()
print("Numeric conversion non-null count:", num_nonnull)

if num_nonnull > 0:
    # Use numeric times
    time = np.round(time_numeric.to_numpy(), 2)
else:
    # Attempt 2: parse known time format "%H.%M.%S.%f" (e.g. '12.34.56.123456')
    try:
        time_dt = pd.to_datetime(df.iloc[:, 0], format="%H.%M.%S.%f", errors='coerce')
        if time_dt.notna().any():
            print("Parsed as time-only with format %H.%M.%S.%f")
            # Convert to elapsed seconds from first timestamp
            elapsed = (time_dt - time_dt.iloc[0]).dt.total_seconds().to_numpy()
            time = np.round(elapsed, 3)
        else:
            raise ValueError("No valid times with that format")
    except Exception as e:
        print("Time-only parse failed:", e)
        # Attempt 3: generic datetime parse
        time_dt = pd.to_datetime(df.iloc[:, 0], errors='coerce', infer_datetime_format=True)
        if time_dt.notna().any():
            print("Parsed as generic datetime")
            time = time_dt
        else:
            raise ValueError("Unable to parse first column as numeric or datetime; inspect the sample values printed above.")

#%%
# Temperature / humidity as numeric arrays
temperature = pd.to_numeric(df.iloc[:, 1], errors='coerce').to_numpy()
humidity = pd.to_numeric(df.iloc[:, 2], errors='coerce').to_numpy()

print("Time array type:", type(time), "shape:", getattr(time, 'shape', None))
print("Temperature non-nulls:", np.count_nonzero(~np.isnan(temperature)))
print("Humidity non-nulls:", np.count_nonzero(~np.isnan(humidity)))

#%%
# Plot: if time is datetime, use plot_date / format axis
plt.figure(figsize=(9,4))
plt.title(f"Temperature Plot for {fn.split('/')[-1].split('_')[0]}")
if np.issubdtype(type(time).__name__ == 'ndarray' and time.dtype, np.number) or isinstance(time, np.ndarray):
    plt.plot(time, temperature, '-o')
    plt.xlabel('Elapsed seconds or numeric time')
else:
    # datetime-like
    plt.plot(time, temperature, '-o')
    plt.gcf().autofmt_xdate()
    plt.xlabel('Time (datetime)')

plt.ylabel('Temperature')
plt.show()

# %%
plt.figure(figsize=(9,4))
plt.title(f"Humidity Plot for {fn.split('/')[-1].split('_')[0]}")
if np.issubdtype(type(time).__name__ == 'ndarray' and time.dtype, np.number) or isinstance(time, np.ndarray):
    plt.plot(time, humidity, '-o')
    plt.xlabel('Elapsed seconds or numeric time')
plt.ylabel('Humidity')
plt.show()
# %%
