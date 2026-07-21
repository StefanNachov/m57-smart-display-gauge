"""Active buzzer control (GPIO). Active buzzer generates its own tone."""
try:
    import RPi.GPIO as GPIO
    _HW = True
except ImportError:
    _HW = False

PIN = 17

class Buzzer:
    def __init__(self, pin=PIN):
        self.pin = pin
        if _HW:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

    def beep(self, duration=0.2):
        if not _HW: return
        import threading, time
        def _b():
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(self.pin, GPIO.LOW)
        threading.Thread(target=_b, daemon=True).start()
