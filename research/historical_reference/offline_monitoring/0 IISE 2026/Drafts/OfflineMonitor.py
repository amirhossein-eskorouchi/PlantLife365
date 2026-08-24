"""
OfflineMonitor.py

Periodically fetches /cam-mid.jpg and /signals from an ESP32 device and
saves frames as .npy plus logs sensor readings to a CSV. Uses background
workers for disk writes and supports graceful shutdown.

Usage:
    python OfflineMonitor.py --device 192.168.4.1 --interval 10 --outdir /path/to/save

Dependencies: requests, numpy, opencv-python
Install example:
    pip install requests numpy opencv-python

"""

import argparse
import requests
import time
import os
import signal
import sys
import threading
import queue
import numpy as np
import cv2
from datetime import datetime
import csv


class SaveWorker(threading.Thread):
    def __init__(self, q):
        super().__init__(daemon=True)
        self.q = q
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            try:
                item = self.q.get(timeout=0.5)
            except queue.Empty:
                continue
            if item is None:
                self.q.task_done()
                break
            path, arr = item
            try:
                tmp = path + '.tmp'
                # write numpy array then atomic replace
                np.save(tmp, arr)
                os.replace(tmp, path)
                print(f"SaveWorker: wrote {path}")
            except Exception as e:
                print(f"SaveWorker error writing {path}: {e}")
            finally:
                self.q.task_done()

    def stop(self):
        self._stop_event.set()


class CsvWorker(threading.Thread):
    def __init__(self, q, csvpath):
        super().__init__(daemon=True)
        self.q = q
        self.csvpath = csvpath
        self._stop_event = threading.Event()
        # ensure header
        if not os.path.exists(self.csvpath):
            try:
                with open(self.csvpath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['time_iso', 'temperature', 'humidity', 'soilMoist', 'radiation'])
            except Exception as e:
                print(f"CsvWorker: failed to create header: {e}")

    def run(self):
        with open(self.csvpath, 'a', newline='') as f:
            writer = csv.writer(f)
            while not self._stop_event.is_set():
                try:
                    row = self.q.get(timeout=0.5)
                except queue.Empty:
                    continue
                if row is None:
                    self.q.task_done()
                    break
                try:
                    writer.writerow(row)
                    f.flush(); os.fsync(f.fileno())
                    print(f"CsvWorker: wrote row {row}")
                except Exception as e:
                    print(f"CsvWorker write error: {e}")
                finally:
                    self.q.task_done()

    def stop(self):
        self._stop_event.set()


class OfflineMonitor:
    def __init__(self, device_ip, interval=10.0, outdir=None, timeout=3.0):
        self.device = device_ip
        self.interval = float(interval)
        self.timeout = float(timeout)
        self.outdir = outdir or os.path.join(os.getcwd(), 'monitor_output')
        os.makedirs(self.outdir, exist_ok=True)

        date_str = datetime.now().strftime('%Y%m%d')
        self.csv_file = os.path.join(self.outdir, f'{date_str}_DetectionLog.csv')

        # queues and workers
        self.save_q = queue.Queue(maxsize=500)
        self.csv_q = queue.Queue(maxsize=2000)
        self.save_worker = SaveWorker(self.save_q)
        self.csv_worker = CsvWorker(self.csv_q, self.csv_file)
        self._stop = False

    def start(self):
        print(f"Starting OfflineMonitor for device {self.device}, saving to {self.outdir}")
        self.save_worker.start()
        self.csv_worker.start()
        # register signals
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        self._run_loop()

    def _handle_signal(self, signum, frame):
        print(f"Signal {signum} received — shutting down gracefully")
        self._stop = True

    def _fetch_signals(self):
        url = f'http://{self.device}/signals'
        try:
            r = requests.get(url, timeout=self.timeout)
            if r.status_code != 200:
                print(f"_fetch_signals: non-200 {r.status_code}")
                return None
            # try parse JSON or CSV-like text
            try:
                j = r.json()
                if isinstance(j, dict):
                    temp = j.get('temperature') or j.get('temp') or j.get('t')
                    hum = j.get('humidity') or j.get('h')
                    soil = j.get('soilMoist') or j.get('soil')
                    rad = j.get('radiation') or j.get('rad')
                    return temp, hum, soil, rad
                elif isinstance(j, (list, tuple)) and len(j) >= 4:
                    return j[0], j[1], j[2], j[3]
            except Exception:
                txt = r.text.strip()
                parts = [p.strip() for p in txt.split(',') if p.strip()!='']
                vals = [None, None, None, None]
                for i in range(min(len(parts), 4)):
                    try:
                        vals[i] = float(parts[i])
                    except Exception:
                        vals[i] = parts[i]
                return tuple(vals)
        except Exception as e:
            print(f"_fetch_signals exception: {e}")
            return None

    def _fetch_frame(self):
        url = f'http://{self.device}/cam-mid.jpg'
        try:
            r = requests.get(url, timeout=self.timeout)
            if r.status_code != 200 or not r.content:
                print(f"_fetch_frame: non-200 or empty: {r.status_code}")
                return None
            arr = np.frombuffer(r.content, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                print("_fetch_frame: decode failed")
                return None
            return img
        except Exception as e:
            print(f"_fetch_frame exception: {e}")
            return None

    def _run_loop(self):
        session = requests.Session()
        next_time = time.time()
        while not self._stop:
            now = time.time()
            if now < next_time:
                time.sleep(min(0.2, next_time - now))
                continue

            ts = datetime.now()
            iso_ts = ts.isoformat()

            # fetch sensors
            sig = self._fetch_signals()
            if sig is None:
                temp = humidity = soil = radiation = None
            else:
                temp, humidity, soil, radiation = sig

            # fetch frame
            frame = self._fetch_frame()
            if frame is not None:
                fname = os.path.join(self.outdir, f"Frame_{ts.strftime('%H.%M.%S.%f')}.npy")
                try:
                    self.save_q.put_nowait((fname, frame.copy()))
                except queue.Full:
                    print("save_q full; dropping frame save")

            # enqueue CSV row
            try:
                row = [iso_ts, temp, humidity, soil, radiation]
                self.csv_q.put_nowait(row)
            except queue.Full:
                print("csv_q full; dropping csv row")

            print(f"Logged {iso_ts} temp={temp} hum={humidity} soil={soil} rad={radiation}")

            next_time = now + self.interval

        # shutdown sequence: flush queues
        print("Shutting down - flushing queues")
        # put sentinels
        try:
            self.save_q.put_nowait(None)
        except Exception:
            pass
        try:
            self.csv_q.put_nowait(None)
        except Exception:
            pass

        # wait for workers to finish
        self.save_worker.join(timeout=5)
        self.csv_worker.join(timeout=5)
        print("OfflineMonitor stopped")


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--device', required=True, help='Device IP or host (e.g. 192.168.4.1)')
    p.add_argument('--interval', type=float, default=10.0, help='Seconds between saves')
    p.add_argument('--outdir', default=None, help='Directory to store .npy and CSV')
    p.add_argument('--timeout', type=float, default=3.0, help='HTTP request timeout (s)')
    args = p.parse_args()

    mon = OfflineMonitor(args.device, interval=args.interval, outdir=args.outdir, timeout=args.timeout)
    try:
        mon.start()
    except KeyboardInterrupt:
        print('KeyboardInterrupt')
        mon._stop = True
        time.sleep(0.5)
    except Exception as e:
        print(f"Monitor failed: {e}")
        sys.exit(2)
