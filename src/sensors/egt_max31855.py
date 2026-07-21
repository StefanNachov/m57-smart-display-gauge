"""Optional pre/post-turbine EGT via MAX31855 K-type thermocouple amplifier.

Shares the SPI bus with the CAN HAT using a dedicated chip-select (GPIO16).
Alert thresholds are location-aware (pre-turbine vs downpipe).
"""
import time
try:
    import RPi.GPIO as GPIO
    _HW = True
except ImportError:
    _HW = False

LIMITS = {
    "pre_turbine":  {"amber": 650, "red": 700, "crit": 720},
    "post_turbine": {"amber": 430, "red": 455, "crit": 470},
}


class EGTProbe:
    def __init__(self, cs=16, clk=11, miso=9, location="pre_turbine"):
        self.cs, self.clk, self.miso = cs, clk, miso
        self.limits = LIMITS[location]
        if _HW:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(cs, GPIO.OUT, initial=GPIO.HIGH)
            GPIO.setup(clk, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(miso, GPIO.IN)

    def _raw(self):
        GPIO.output(self.cs, GPIO.LOW); time.sleep(0.001)
        v = 0
        for _ in range(32):
            GPIO.output(self.clk, GPIO.HIGH); time.sleep(1e-5)
            v = (v << 1) | GPIO.input(self.miso)
            GPIO.output(self.clk, GPIO.LOW); time.sleep(1e-5)
        GPIO.output(self.cs, GPIO.HIGH)
        return v

    def read(self):
        if not _HW: return None
        v = self._raw()
        if v & 0x7:            # fault bits: open / short-gnd / short-vcc
            return None
        t = v >> 18
        if t & 0x2000: t -= 0x4000
        return t * 0.25
