"""
hog.py - presentation helper. Makes ONE process behave abnormally on purpose so the
detector has something real to catch. It does no detecting itself.

  Phase 1  behaves normally (steady memory, idle CPU) so the detector can learn "normal"
  Phase 2  ANOMALY: memory climbs to the peak and the CPU is loaded on all cores
  Phase 3  goes back to normal, so you can also show the alert clearing

Usage (any folder, with monitor + detector already running):
    python hog.py
    python hog.py --baseline 120 --peak-mb 1800 --hold 90
"""
import argparse
import threading
import time

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--baseline", type=int, default=150, help="seconds of normal behaviour first")
ap.add_argument("--base-mb", type=int, default=300, help="memory held while 'normal'")
ap.add_argument("--peak-mb", type=int, default=1500, help="memory reached during the anomaly")
ap.add_argument("--hold", type=int, default=60, help="seconds to stay abnormal at the peak")
ap.add_argument("--recover", type=int, default=30, help="seconds of normal behaviour at the end")
a = ap.parse_args()


def alloc(mb):
    # filled with a value so the pages are touched and count in the working set (Memory_MB)
    return bytearray(b"\x01") * (mb * 1024 * 1024)


stop = threading.Event()


def burn():
    m = np.random.rand(1500, 1500)
    while not stop.is_set():
        m @ m            # numpy runs this on all cores, so CPU_Percent jumps too


held = [alloc(a.base_mb)]
print(f"Phase 1: normal behaviour at {a.base_mb} MB. Let the detector learn this.")
left = a.baseline
while left > 0:
    print(f"   anomaly starts in {left}s", flush=True)
    step = min(10, left)
    time.sleep(step)
    left -= step

print("Phase 2: ANOMALY - memory and CPU spike now. Watch the detector.", flush=True)
threading.Thread(target=burn, daemon=True).start()
total = a.base_mb
while total < a.peak_mb:
    held.append(alloc(200))
    total += 200
    print(f"   holding {total} MB", flush=True)
    time.sleep(3)
time.sleep(a.hold)

stop.set()
held.clear()
held = [alloc(a.base_mb)]
print(f"Phase 3: back to normal ({a.base_mb} MB, idle). The alert should clear.", flush=True)
time.sleep(a.recover)
print("Done.")
