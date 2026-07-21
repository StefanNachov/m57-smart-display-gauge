"""FastLifeBG M57 Gauge — entry point.

Wires together: CAN reader -> ECUData -> alert engine -> (buzzer, display, logger).
Runs the main loop. Display/logging hooks are modular so the core can run headless.
"""
import time
from ecu_data import ECUData
from can_reader import CanReader, bring_up
from alert_engine import AlertEngine
from buzzer import Buzzer
from relay import IsolationRelay


def main():
    bring_up("can0", 500000)

    data = ECUData()
    buzzer = Buzzer()
    relay = IsolationRelay()          # CAN connected by default
    alerts = AlertEngine(buzzer=buzzer)
    reader = CanReader(data, "can0")

    # optional: from display.ui import UI; ui = UI(data, alerts, relay)
    # optional: from logger import Logger; log = Logger(data, alerts)

    last_check = 0.0
    try:
        while True:
            reader.poll_once(timeout=1.0)
            now = time.time()
            if now - last_check >= 0.2:      # 5 Hz alert + UI cadence
                alerts.check(data)
                # ui.render(); log.tick()
                last_check = now
    except KeyboardInterrupt:
        pass
    finally:
        reader.shutdown()


if __name__ == "__main__":
    main()
