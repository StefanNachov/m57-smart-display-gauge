"""SocketCAN interface: reads frames, dispatches to decoders, updates ECUData."""
import subprocess
import can
from decoders import DECODERS
from ecu_data import ECUData


def bring_up(channel="can0", bitrate=500000):
    subprocess.run(["sudo", "ip", "link", "set", channel, "down"],
                   stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "ip", "link", "set", channel, "up", "type", "can",
                    "bitrate", str(bitrate), "restart-ms", "100"], check=True)


class CanReader:
    def __init__(self, data: ECUData, channel="can0"):
        self.data = data
        self.bus = can.interface.Bus(channel=channel, bustype="socketcan")

    def poll_once(self, timeout=1.0):
        msg = self.bus.recv(timeout=timeout)
        if msg is None:
            return
        dec = DECODERS.get(msg.arbitration_id)
        if dec:
            for k, v in dec(list(msg.data)).items():
                setattr(self.data, k, v)
            self.data.touch()

    def shutdown(self):
        self.bus.shutdown()
