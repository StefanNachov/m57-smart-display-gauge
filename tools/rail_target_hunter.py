"""Locate the rail-pressure TARGET byte empirically.

Method: on a throttle transient, the ECU commands a higher target and physical
rail pressure follows ~100-300 ms later. This tool watches every (ID, byte) in a
short window before each rise in rail ACTUAL (0x3B4) and reports which byte
consistently rises first. Run engine at idle, do sharp throttle stabs.
"""
import subprocess, time
from collections import defaultdict, deque

subprocess.run("sudo ip link set can0 up type can bitrate 500000 restart-ms 100",
               shell=True)
import can
bus = can.interface.Bus(channel="can0", bustype="socketcan")

WINDOW, RISE = 0.6, 80
hist = deque(); rail_prev = None; scores = defaultdict(int); events = 0
print("Do sharp throttle stabs (x3-5). Ctrl+C for results.")
try:
    while True:
        m = bus.recv(timeout=1.0)
        if not m: continue
        now = time.time()
        hist.append((now, m.arbitration_id, bytes(m.data)))
        while hist and now - hist[0][0] > WINDOW: hist.popleft()
        if m.arbitration_id == 0x3B4 and len(m.data) >= 2:
            rail = ((m.data[0] << 8) | m.data[1]) * 0.1
            if rail_prev is not None and rail - rail_prev > RISE:
                events += 1
                first, last = {}, {}
                for (_, cid, data) in hist:
                    for i, b in enumerate(data):
                        k = (cid, i)
                        first.setdefault(k, b); last[k] = b
                for k in first:
                    cid, i = k
                    if cid == 0x3B4 and i in (0, 1): continue
                    if last[k] - first[k] > 15: scores[k] += 1
            rail_prev = rail
except KeyboardInterrupt:
    print(f"\n{events} events")
    for (cid, i), n in sorted(scores.items(), key=lambda x: -x[1])[:10]:
        flag = "  <== LIKELY TARGET" if n == events and events >= 3 else ""
        print(f"0x{cid:03X} byte{i}: {n}/{events}{flag}")
