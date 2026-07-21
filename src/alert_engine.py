"""Deviation-based + threshold alert engine.

Boost and rail alerts compare actual vs the ECU's own commanded target, so they
hold across any state of tune. Each alert must persist for a hold time before
firing (debounce). Critical alerts trigger the buzzer.
"""
from time import time

# tuning parameters
BOOST_DEV_AMBER, BOOST_DEV_RED = 0.15, 0.30      # bar below target
OVERBOOST_RED = 0.20                              # bar above target
RAIL_DEV_AMBER, RAIL_DEV_RED = 200, 400          # bar below target
COOLANT_A, COOLANT_R = 105, 110
OIL_A, OIL_R = 125, 135
IAT_A, IAT_R = 60, 75
TRANS_A, TRANS_R = 110, 120
MIN_RPM_FOR_DEV = 1500


class _Alert:
    def __init__(self, name, hold_s):
        self.name, self.hold_s = name, hold_s
        self.since = None
        self.level = None

    def update(self, level_now):
        now = time()
        fired = None
        if level_now is None:
            self.since = None
            if self.level:
                fired = ("CLEAR", self.name)
            self.level = None
        else:
            if self.since is None:
                self.since = now
            elif now - self.since >= self.hold_s and self.level != level_now:
                self.level = level_now
                fired = (level_now, self.name)
        return fired


class AlertEngine:
    def __init__(self, buzzer=None):
        self.buzzer = buzzer
        self.alerts = {
            "boost_under": _Alert("BOOST UNDERDELIVERY", 2.0),
            "overboost":   _Alert("OVERBOOST", 1.0),
            "rail_under":  _Alert("RAIL PRESSURE DROP", 2.0),
            "coolant":     _Alert("COOLANT TEMP", 3.0),
            "oil":         _Alert("OIL TEMP", 3.0),
            "iat":         _Alert("IAT HEAT SOAK", 3.0),
            "trans":       _Alert("TRANS TEMP", 3.0),
        }
        self.active = []

    @staticmethod
    def _band(v, a, r):
        if v is None: return None
        if v >= r: return "RED"
        if v >= a: return "AMBER"
        return None

    def check(self, d):
        events = []
        rev = d.rpm > MIN_RPM_FOR_DEV

        lvl = None
        if rev and d.boost_target_bar > 0.3:
            dev = d.boost_target_bar - d.boost_actual_bar
            lvl = "RED" if dev >= BOOST_DEV_RED else "AMBER" if dev >= BOOST_DEV_AMBER else None
        events.append(self.alerts["boost_under"].update(lvl))

        lvl = None
        if rev and d.boost_target_bar > 0.3:
            if d.boost_actual_bar - d.boost_target_bar >= OVERBOOST_RED:
                lvl = "RED"
        events.append(self.alerts["overboost"].update(lvl))

        lvl = None
        if rev and d.rail_target_bar is not None:
            dev = d.rail_target_bar - d.rail_actual_bar
            lvl = "RED" if dev >= RAIL_DEV_RED else "AMBER" if dev >= RAIL_DEV_AMBER else None
        events.append(self.alerts["rail_under"].update(lvl))

        events.append(self.alerts["coolant"].update(self._band(d.coolant_c, COOLANT_A, COOLANT_R)))
        events.append(self.alerts["oil"].update(self._band(d.oil_c, OIL_A, OIL_R)))
        events.append(self.alerts["iat"].update(self._band(d.iat_c, IAT_A, IAT_R)))
        events.append(self.alerts["trans"].update(self._band(d.trans_c, TRANS_A, TRANS_R)))

        for ev in events:
            if ev:
                self._handle(ev)
        self.active = [a.name for a in self.alerts.values() if a.level]

    def _handle(self, ev):
        level, name = ev
        if level == "RED" and self.buzzer:
            self.buzzer.beep()
        # hook: log to alert file, update display banner, etc.
