# Wiring Reference

Full pinout and connection detail. All GPIO numbers are BCM.

## Power
```
Vehicle switched 12V --> fuse tap (2A) --> LM2596S (set 5.1V) --> Pi 5V (Pin 2/4)
Vehicle chassis GND -----------------------------------------> Pi GND (Pin 6/9)
```
Set LM2596S output to 5.1 V (measured) before connecting. Confirm no undervoltage
with `vcgencmd get_throttled` returning `0x0`.

## CAN HAT (Waveshare RS485/CAN, MCP2515 + SN65HVD230)
- Mounts on 40-pin header; uses SPI0 CE0 + INT (GPIO25).
- **120 R termination jumpers OFF** (vehicle provides termination).
- CAN wires: **H** terminal, **L** terminal.
- Vehicle tap: X14271 pins 1/2, or OBD-II pins 6 (H) / 14 (L). Confirm ~60 Ohm
  across the pair, ignition off.

## ILI9341 display + XPT2046 touch (SPI0, separate chip-selects)
| Signal | Pi pin | GPIO |
|--------|--------|------|
| VCC 3.3V | 17 | - |
| GND | 20 | - |
| SCK | 23 | 11 |
| MOSI | 19 | 10 |
| MISO | 21 | 9 |
| Display CS | 26 | 7 (CE1) |
| DC/RS | 18 | 24 |
| RESET | 22 | 25* |
| Backlight LED | 12 | 18 (PWM) |
| Touch T_CS | 29 | 5 |
| Touch T_IRQ | 31 | 6 |

*Avoid colliding with the CAN HAT INT pin (GPIO25); re-map RESET if needed.

## Buzzer (active, 3-pin)
| Signal | Pi pin | GPIO |
|--------|--------|------|
| VCC 5V | 4 | - |
| GND | 14 | - |
| Signal | 11 | 17 |

## Isolation relay
| Signal | Pi pin | GPIO |
|--------|--------|------|
| VCC 5V | 2 | - |
| GND | 6 | - |
| IN | 13 | 27 |
NO/COM in series on CAN H (and L) between tap and HAT.

## Optional: MAX31855 EGT (SPI0, own CS)
| Signal | Pi pin | GPIO |
|--------|--------|------|
| VIN 3.3V | 1 | - |
| GND | 9 | - |
| SCK | 23 | 11 (shared) |
| SO | 21 | 9 (shared) |
| CS | 36 | 16 |

## Optional: MCP3008 ADC for oil pressure (SPI0, CE1 or own CS)
Standard MCP3008 SPI wiring; analog 0-10 bar sender on CH0.
