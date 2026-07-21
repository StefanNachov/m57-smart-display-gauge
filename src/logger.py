"""CSV + JSON logging with daily rotation and age-based cleanup."""
import csv, json, time
from pathlib import Path
from datetime import datetime, timedelta

LOG_DIR = Path("/var/log/fastlifebg")
KEEP_DAYS = 30


class Logger:
    def __init__(self, data, alerts):
        self.data, self.alerts = data, alerts
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self._cleanup()
        self.day = datetime.now().date()
        self._open()

    def _cleanup(self):
        cutoff = datetime.now() - timedelta(days=KEEP_DAYS)
        for f in LOG_DIR.glob("*.csv"):
            if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                f.unlink()

    def _open(self):
        name = LOG_DIR / f"engine_{self.day}.csv"
        new = not name.exists()
        self.fh = open(name, "a", newline="")
        self.w = csv.writer(self.fh)
        if new:
            self.w.writerow(["timestamp", "rpm", "boost_act", "boost_tgt",
                             "coolant", "oil", "iat", "rail_act", "fuel",
                             "gear", "trans", "speed"])

    def tick(self):
        if datetime.now().date() != self.day:      # midnight rotation
            self.fh.close(); self.day = datetime.now().date(); self._open()
        d = self.data
        self.w.writerow([datetime.now().isoformat(timespec="milliseconds"),
                         d.rpm, d.boost_actual_bar, d.boost_target_bar,
                         d.coolant_c, d.oil_c, d.iat_c, d.rail_actual_bar,
                         d.fuel_lph, d.gear, d.trans_c, d.speed_kph])
        self.fh.flush()
