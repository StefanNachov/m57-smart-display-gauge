"""Bring-up + bus discovery utility. Lists all CAN IDs seen with rate + sample."""
import subprocess, sys, time
from collections import defaultdict

subprocess.run("sudo ip link set can0 up type can bitrate 500000 restart-ms 100",
               shell=True)
import can
bus = can.interface.Bus(channel="can0", bustype="socketcan")

seen, counts = {}, defaultdict(int)
t0 = time.time()
print("Scanning — Ctrl+C to stop")
try:
    while True:
        m = bus.recv(timeout=1.0)
        if m:
            counts[m.arbitration_id] += 1
            if m.arbitration_id not in seen:
                seen[m.arbitration_id] = m.data.hex()
                print(f"NEW 0x{m.arbitration_id:03X}  {m.data.hex()}")
except KeyboardInterrupt:
    dur = time.time() - t0
    print(f"\n{len(seen)} unique IDs in {dur:.0f}s")
    for cid in sorted(seen):
        print(f"0x{cid:03X}  {counts[cid]/dur:6.1f}/s  {seen[cid]}")
