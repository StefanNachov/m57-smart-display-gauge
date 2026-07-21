# M57 Digital Gauge — CAN Bus Engine Monitor for BMW Diesel

A custom digital instrument cluster for BMW M57/N57 diesel engines (E60/E61/E9x
chassis), built on a Raspberry Pi. It passively reads the car's powertrain CAN
bus in real time and renders live engine data on a touchscreen, with configurable
audible and visual alerts tuned for high-performance and remapped engines.

Designed for tuned builds where factory instrumentation is insufficient — the
system reads the ECU's own target values (boost, rail pressure) directly off the
bus and alerts on **deviation**, so it adapts to any state of tune without
reconfiguration.

![status](https://img.shields.io/badge/status-active_development-blue)
![platform](https://img.shields.io/badge/platform-Raspberry_Pi-c51a4a)
![language](https://img.shields.io/badge/language-Python_3-3776ab)

---

## Table of Contents

- [Features](#features)
- [Hardware](#hardware)
- [System Architecture](#system-architecture)
- [Wiring](#wiring)
- [Software Setup](#software-setup)
- [CAN Bus Protocol](#can-bus-protocol)
- [Alert Engine](#alert-engine)
- [Display Pages](#display-pages)
- [Optional Sensors](#optional-sensors)
- [Repository Structure](#repository-structure)
- [Engineering Notes](#engineering-notes)
- [Roadmap](#roadmap)

---

## Features

- **Passive CAN bus reading** — listens to the BMW PT-CAN at 500 kbps without
  transmitting, so it cannot disturb the vehicle bus during normal operation.
- **Live engine data** — RPM, boost (actual + target), coolant, intake air temp,
  oil temp, rail pressure, fuel consumption, gear, transmission fluid temp,
  vehicle speed, engine torque.
- **Deviation-based alerts** — boost and rail pressure alerts compare the ECU's
  actual vs its own commanded target, so they work on any remap automatically.
- **Touchscreen UI** — multi-page interface on an SPI ILI9341 display with
  XPT2046 touch, navigable by touch.
- **Audible alerts** — active buzzer for critical conditions (rail pressure
  collapse, overboost, over-temperature).
- **Hardware diagnostic isolation** — a GPIO-controlled relay physically
  disconnects the CAN interface during ECU flashing, eliminating any risk of the
  gauge glitching the bus while a remap is being written.
- **Optional add-on sensors** — real oil pressure (analog sender + ADC) and
  exhaust gas temperature (K-type thermocouple), for builds beyond factory
  sensor coverage.
- **Data logging** — CSV engine/transmission logs, event-based alert logs, and
  per-drive JSON session summaries, with automatic rotation.

---

## Hardware

| Component | Purpose |
|-----------|---------|
| Raspberry Pi (Zero 2 W / 3 / 4) | Main compute — runs the display and CAN stack |
| Waveshare RS485/CAN HAT (MCP2515 + SN65HVD230) | CAN controller + transceiver |
| ILI9341 2.4" SPI display (with XPT2046 touch) | Touchscreen instrument display |
| Active buzzer module (3.3–5 V) | Audible alerts |
| 5 V relay module | Hardware CAN isolation for ECU flashing |
| LM2596S DC-DC converter | 12 V → 5.1 V regulated power from vehicle |
| Add-a-circuit fuse tap | Switched 12 V supply |
| T-tap connectors + twisted pair | Non-destructive CAN bus tap |

### Why the SN65HVD230 transceiver

The controller (MCP2515) runs at 3.3 V to match the Pi's GPIO logic; the CAN
transceiver must interface the physical bus. Cheap combined boards using the
TJA1050 tie both chips to a single 5 V rail, which creates a logic-level and
ground-reference conflict — on a vehicle these boards frequently initialise
correctly (loopback passes) yet fail to receive real bus traffic. The
SN65HVD230 is a native 3.3 V transceiver, so controller, transceiver, and Pi all
share one voltage domain and one ground reference. This eliminates the failure
class entirely and is the correct choice for a deployed product. See
[docs/ENGINEERING_NOTES.md](docs/ENGINEERING_NOTES.md) for the full debugging
story.

---

## System Architecture

```
                    ┌──────────────────────────────┐
   BMW PT-CAN ──────┤  T-tap  →  CAN HAT (MCP2515)  │
   (500 kbps)       │            SN65HVD230 xcvr    │
                    └───────────────┬──────────────┘
                                    │ SPI (CE0)
                    ┌───────────────┴──────────────┐
   12 V fused ──►   │        Raspberry Pi          │
   LM2596S 5.1 V    │  ┌────────────────────────┐  │
                    │  │  can_reader (SocketCAN)│  │
                    │  │        │               │  │
                    │  │   ECUData model        │  │
                    │  │        │               │  │
                    │  │   alert_engine ────────┼──┼──► buzzer (GPIO)
                    │  │        │               │  │
                    │  │   display (pages) ─────┼──┼──► ILI9341 (SPI CE1)
                    │  │        │               │  │◄── XPT2046 touch
                    │  │   logger ──────────────┼──┼──► CSV / JSON logs
                    │  └────────────────────────┘  │
                    │   relay control ─────────────┼──► CAN isolation relay
                    └──────────────────────────────┘
```

Data flows one direction for normal operation: CAN → decode → model → (display,
alerts, logging). The only outputs are the buzzer, display, logs, and the
isolation relay. The CAN interface runs in **listen-only** mode by default.

---

## Wiring

### CAN HAT → Raspberry Pi
The HAT mounts on the 40-pin header and uses SPI0. No manual wiring required;
it routes SCK/MOSI/MISO/CE0/INT and power internally.

- **120 Ω termination jumpers: OFF** — the vehicle already provides two 120 Ω
  terminators (measure ~60 Ω across CAN H/L to confirm). Adding a third corrupts
  bus impedance.
- CAN H → screw terminal **H**, CAN L → screw terminal **L**.

### Vehicle CAN tap (BMW E60/E9x)
- Connector **X14271** (behind glove box) or OBD-II pins 6 (CAN-H) and 14 (CAN-L).
- Confirm the pair by measuring **~60 Ω** across the two wires, ignition off.

### ILI9341 Display + XPT2046 Touch (shared SPI0 bus, separate chip-selects)

| Display pin | Pi pin | GPIO | Notes |
|-------------|--------|------|-------|
| VCC | 17 | 3.3 V | |
| GND | 20 | GND | |
| SCK | 23 | GPIO11 | shared SPI clock |
| MOSI | 19 | GPIO10 | shared |
| MISO | 21 | GPIO9 | shared |
| CS (display) | 26 | GPIO7 (CE1) | display chip-select |
| DC/RS | 18 | GPIO24 | data/command |
| RESET | 22 | GPIO25 | *(see note)* |
| LED | 12 | GPIO18 | PWM backlight |
| T_CS (touch) | 29 | GPIO5 | touch chip-select |
| T_IRQ (touch) | 31 | GPIO6 | touch interrupt |

> RESET/INT pin assignments must avoid the pin the CAN HAT uses for its INT
> line (commonly GPIO25). Re-map as required for your HAT revision.

### Buzzer

| Buzzer pin | Pi pin | GPIO |
|------------|--------|------|
| VCC | 4 | 5 V |
| GND | 14 | GND |
| Signal | 11 | GPIO17 |

### Diagnostic isolation relay

| Relay pin | Connection |
|-----------|------------|
| VCC | 5 V |
| GND | GND |
| IN | GPIO27 (Pin 13) |
| COM / NO | in series on CAN H (and L) between tap and HAT |

`GPIO27 HIGH` = relay closed = normal. `GPIO27 LOW` = open = CAN physically
isolated for safe ECU flashing.

### Power

```
Vehicle switched 12 V ─► fuse tap (2 A) ─► LM2596S (set to 5.1 V) ─► Pi 5 V / GND
Vehicle chassis ground ────────────────────────────────────────────► Pi GND
```

Use a **switched** fuse so the Pi powers down with the ignition. Set the LM2596S
to **5.1 V** (measured) before connecting — this compensates for cable/connector
drop and keeps the Pi above its 4.63 V undervoltage threshold under load.

---

## Software Setup

Raspberry Pi OS Lite (32-bit for Pi Zero/1, 64-bit fine for Pi 3/4).

Enable SPI and the MCP2515 overlay in `/boot/firmware/config.txt`:

```
dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25
```

> **Match the oscillator to your HAT's crystal.** The Waveshare RS485 CAN HAT
> uses a **12 MHz** crystal (`oscillator=12000000`). Many bare modules use 8 MHz.
> A mismatch produces a silent, error-free bus that receives nothing — verify
> with `ip -details link show can0 | grep clock`.

Install dependencies:

```bash
sudo apt update
sudo apt install -y can-utils python3-can python3-spidev python3-rpi.gpio \
                    python3-pip python3-pil
pip3 install luma.lcd --break-system-packages
```

Bring up the interface and verify:

```bash
sudo ip link set can0 up type can bitrate 500000
candump can0          # should stream frames with ignition on
```

Run the gauge:

```bash
python3 src/main.py
```

To start on boot, install the systemd service in `services/`:

```bash
sudo cp services/m57-gauge.service /etc/systemd/system/
sudo systemctl enable --now m57-gauge
```

---

## CAN Bus Protocol

The BMW PT-CAN continuously broadcasts powertrain data at 500 kbps. The same
message IDs apply across the E-series M57/N57 range (E60/E61 525d–535d,
E90/E91/E92/E93 318d–335d, E70 X5, E83 X3). The gauge listens passively; no
requests are needed for live data.

| CAN ID | Content |
|--------|---------|
| `0x0AA` | RPM, accelerator pedal % |
| `0x0A8` | Engine torque (actual) |
| `0x0BA` | Gear position, transmission fluid temp |
| `0x1A0` | Vehicle speed |
| `0x1A2` | Torque converter lockup % |
| `0x1B6` | Oil temperature |
| `0x1D0` | Coolant temp, IAT, **boost actual + boost target** |
| `0x3B4` | Rail pressure (actual), fuel consumption |

Fault codes (DTCs) are not broadcast; they are read on demand via OBD-II
request/response (`0x7DF` → `0x7E8`/`0x7E9`) over the same interface, with
ISO-TP multi-frame reassembly.

> Byte offsets and scaling factors are validated against live vehicle data
> during commissioning — see `docs/CAN_MAP.md`. Values sourced from community
> reverse-engineering are marked for verification rather than assumed correct.

---

## Alert Engine

Alerts are **deviation-based** where the ECU broadcasts a target, so they hold
across any state of tune (stock through hybrid-turbo / large-injector builds)
without reconfiguration.

| Alert | Condition | Level |
|-------|-----------|-------|
| Boost underdelivery | actual < target − 0.15 bar for 2 s | Amber |
| Boost failure | actual < target − 0.30 bar for 2 s | Red + buzzer |
| Overboost | actual > target + 0.20 bar for 1 s | Red + buzzer |
| Rail pressure drop | actual < target − 200 bar for 2 s | Amber |
| Rail pressure collapse | actual < target − 400 bar for 2 s | Red + buzzer |
| Coolant temp | > 105 / 110 °C | Amber / Red |
| Oil temp | > 125 / 135 °C | Amber / Red |
| IAT (heat soak) | > 60 / 75 °C | Amber / Red |
| Trans fluid temp | > 110 / 120 °C | Amber / Red |

Each alert requires its condition to persist for a hold time before firing,
suppressing false positives from transient spikes. Deviation checks are gated
above a minimum RPM to ignore idle/overrun noise.

The rail-pressure collapse alert is the most safety-relevant for high-fuel
builds (upgraded CP3/dual-pump setups): a pump falling behind demand under load
risks a lean condition and piston damage that no factory instrument surfaces.

---

## Display Pages

1. **Live Engine** — boost (actual vs target, auto-scaled), RPM, oil/coolant/IAT,
   rail pressure, gear, load.
2. **Engine Health** — rail pressure trend graph (pump health), fuel rate,
   battery voltage, oil pressure status, fault-code count.
3. **Performance Timers** — 0–100, 0–200, 100–200, peak boost, using wheel-speed
   data for launch/rolling triggers.
4. **Transmission** — gear, fluid temp with thresholds, TCC lockup %, shift
   monitoring.
5. **Settings** — brightness, theme, rail-pressure scale (per sender),
   speedometer correction, diagnostic-mode toggle.
6. **Fault Codes** — engine/transmission DTCs via OBD-II, read on a 60 s cycle.

---

## Optional Sensors

Parameters outside factory CAN coverage are supported as add-on SPI sensors that
coexist with the CAN HAT on the shared SPI bus:

- **Oil pressure (real value)** — the factory M57 sensor is a switch (OK/low
  status only). A 0–10 bar analog sender via an MCP3008 ADC provides a true bar
  reading.
- **Exhaust gas temperature** — via MAX31855 + K-type thermocouple. Alert
  thresholds are location-aware: pre-turbine (manifold, ~677 °C redline) vs
  post-turbine (downpipe, ~455 °C redline), since EGT drops ~200–300 °C across
  the turbine and the two locations cannot share a limit.

DPF-equipped cars also expose factory EGT sensors (before-cat / before-DPF) via
OBD-II polling — useful for exhaust/regen monitoring, though post-turbo and not
a substitute for a pre-turbine probe on tuned engines.

---

## Repository Structure

```
m57-gauge-project/
├── README.md                  # this file
├── LICENSE
├── docs/
│   ├── CAN_MAP.md             # full CAN ID / byte / scaling reference
│   ├── WIRING.md              # detailed wiring + pinouts
│   └── ENGINEERING_NOTES.md   # debugging log, design decisions
├── src/
│   ├── main.py                # entry point / main loop
│   ├── can_reader.py          # SocketCAN interface + frame dispatch
│   ├── decoders.py            # per-ID decode functions -> ECUData
│   ├── ecu_data.py            # ECUData dataclass (shared state)
│   ├── alert_engine.py        # deviation + threshold alert logic
│   ├── display/
│   │   ├── ui.py              # page manager + touch handling
│   │   └── pages.py           # individual page renderers
│   ├── sensors/
│   │   ├── egt_max31855.py    # optional EGT probe
│   │   └── oilpress_mcp3008.py# optional oil pressure sender
│   ├── buzzer.py              # GPIO buzzer control
│   ├── relay.py               # diagnostic isolation relay
│   └── logger.py              # CSV/JSON logging + rotation
├── tools/
│   ├── can_tester.py          # bring-up + bus discovery utility
│   └── rail_target_hunter.py  # correlation tool to find rail-target byte
├── services/
│   └── m57-gauge.service      # systemd unit
└── config/
    └── settings.example.json  # per-vehicle configuration
```

---

## Engineering Notes

Selected decisions documented in full in
[docs/ENGINEERING_NOTES.md](docs/ENGINEERING_NOTES.md):

- **Listen-only by default** — the CAN controller is configured in listen-only
  mode for all live monitoring; it is electrically incapable of transmitting,
  guaranteeing the gauge cannot disturb the vehicle bus.
- **Deviation over absolute thresholds** — reading the ECU's own commanded
  targets makes the alert logic tune-agnostic, a key requirement for the
  performance market.
- **Transceiver selection** — the move from TJA1050 to SN65HVD230 resolved a
  class of "initialises but never receives" failures rooted in the 3.3 V/5 V
  single-rail conflict on cheap combined boards.
- **Power integrity** — the Pi's 4.63 V undervoltage threshold makes supply
  quality critical in a vehicle; the design regulates to 5.1 V and shares chassis
  ground so the transceiver's common-mode reference matches the bus.
- **Hardware diagnostic isolation** — a physical relay, rather than a software
  flag, guarantees zero CAN presence during ECU flashing.

---

## Roadmap

- [ ] Finalise live-validated byte offsets for all decoders
- [ ] Locate and confirm rail-pressure target byte (correlation tool in `tools/`)
- [ ] Complete touch UI page set
- [ ] OTA update mechanism for fielded units
- [ ] Port research to related platforms (Audi/VW 3.0 TDI, TFSI)

---

## License

MIT — see [LICENSE](LICENSE).

## Disclaimer

This project taps into a vehicle's CAN bus and is intended for off-road /
track / educational use by users who understand the risks. Incorrect wiring can
damage vehicle electronics. Use at your own risk. Not affiliated with BMW AG.
