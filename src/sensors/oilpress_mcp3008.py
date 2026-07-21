"""Optional real oil pressure via 0-10 bar analog sender + MCP3008 ADC (SPI).

Factory M57 oil pressure sensor is a switch (status only); this provides a true
bar reading for high-power builds.
"""
try:
    import spidev
    _HW = True
except ImportError:
    _HW = False


class OilPressure:
    def __init__(self, channel=0, bus=0, device=1, vref=3.3, bar_per_volt=4.0):
        self.channel, self.vref, self.k = channel, vref, bar_per_volt
        if _HW:
            self.spi = spidev.SpiDev(); self.spi.open(bus, device)
            self.spi.max_speed_hz = 1_000_000

    def read_bar(self):
        if not _HW: return None
        r = self.spi.xfer2([1, (8 + self.channel) << 4, 0])
        raw = ((r[1] & 3) << 8) | r[2]
        volts = raw * self.vref / 1023.0
        return round(volts * self.k, 2)
