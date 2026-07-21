"""Diagnostic isolation relay. GPIO HIGH = CAN connected, LOW = isolated."""
try:
    import RPi.GPIO as GPIO
    _HW = True
except ImportError:
    _HW = False

PIN = 27

class IsolationRelay:
    def __init__(self, pin=PIN):
        self.pin = pin
        if _HW:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)  # connected by default
        self.connected = True

    def connect(self):
        if _HW: GPIO.output(self.pin, GPIO.HIGH)
        self.connected = True

    def isolate(self):
        """Physically disconnect CAN for safe ECU flashing."""
        if _HW: GPIO.output(self.pin, GPIO.LOW)
        self.connected = False
