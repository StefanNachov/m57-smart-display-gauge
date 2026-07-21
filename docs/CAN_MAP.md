# CAN Message Reference — BMW M57/N57 PT-CAN

Bus: **PT-CAN, 500 kbps, standard 11-bit identifiers.**
Applies across the E-series M57/N57 range (E60/E61, E90/E91/E92/E93, E70, E83).
All live data is broadcast continuously; the gauge reads it passively.

> **Validation status.** Byte offsets and scaling factors below are drawn from
> community reverse-engineering and are validated against live vehicle data
> during commissioning. Fields not yet confirmed on-vehicle are marked
> *(verify)*. The `tools/rail_target_hunter.py` utility is provided to locate
> the rail-pressure target byte empirically.

---

## Broadcast messages (passive read)

### `0x0AA` — Engine speed / pedal
| Bytes | Field | Decode |
|-------|-------|--------|
| 0–1 | RPM | `((B0<<8)|B1) * 0.25` |
| 2 | Accelerator pedal % | `B2 * 0.392` |

### `0x0A8` — Engine torque
| Bytes | Field | Decode |
|-------|-------|--------|
| 1–2 | Actual torque (Nm) | `((B2<<8)|B1) * 0.03125` *(verify)* |

### `0x0BA` — Transmission (EGS)
| Bytes | Field | Decode |
|-------|-------|--------|
| 0 (low nibble) | Gear | 0=P,1=R,2=N,3=D,4–9=1–6 |
| 5 | Trans fluid temp (°C) | `B5 - 48` *(verify)* |

### `0x1A0` — Vehicle speed (DSC)
| Bytes | Field | Decode |
|-------|-------|--------|
| 0–1 | Speed (kph) | `((B0<<8)|B1) * 0.01` *(verify)* |

### `0x1A2` — Torque converter
| Bytes | Field | Decode |
|-------|-------|--------|
| — | TCC lockup % | *(verify)* |

### `0x1B6` — Oil temperature (DDE)
| Bytes | Field | Decode |
|-------|-------|--------|
| 2 | Oil temp (°C) | `B2 - 48` *(verify)* |

### `0x1D0` — Thermal + boost (DDE) — key message
| Bytes | Field | Decode |
|-------|-------|--------|
| 1 | Coolant temp (°C) | `B1 - 48` *(verify)* |
| 3 | Intake air temp (°C) | `B3 - 48` *(verify)* |
| 4 | Boost actual (bar) | `B4 * 0.01` *(verify)* |
| 5 | Boost target (bar) | `B5 * 0.01` *(verify)* |

### `0x3B4` — Rail pressure + fuel (DDE)
| Bytes | Field | Decode |
|-------|-------|--------|
| 0–1 | Rail pressure actual (bar) | `((B0<<8)|B1) * 0.1` *(verify)* |
| 4 | Fuel consumption (l/h) | `B4 * 0.1` *(verify)* |

Rail pressure **target** is broadcast by the DDE but its message/byte position
is not yet confirmed. It is located empirically by correlating which byte rises
immediately *before* rail actual on a throttle transient — the ECU commands the
target, and physical pressure follows ~100–300 ms later.

---

## On-demand messages (OBD-II request/response)

Fault codes are not broadcast. They are read via standard OBD-II:

```
Request:  0x7DF  [02 03 00 00 00 00 00 00]   (Mode 03 — stored DTCs)
Response: 0x7E8  [ ... ]   engine (DDE)
          0x7E9  [ ... ]   transmission (EGS)
```

Responses spanning more than one frame use ISO-TP (ISO 15765-2) segmentation
and require multi-frame reassembly.

Factory EGT (DPF-equipped cars) via Mode 01:
```
PID 0x78  — Exhaust Gas Temperature Bank 1 (EGT1..4)
PID 0x79  — Exhaust Gas Temperature Bank 2
decode:  ((MSB<<8)|LSB) * 0.1 - 40  °C   per supported sensor
```

---

## Parameter availability summary

| Parameter | Source | Notes |
|-----------|--------|-------|
| RPM, pedal | `0x0AA` | broadcast |
| Boost actual + target | `0x1D0` | both broadcast — enables deviation alerts |
| Coolant, IAT | `0x1D0` | broadcast |
| Oil temperature | `0x1B6` | real sensor |
| Oil pressure (value) | — | factory sensor is a switch; add-on ADC required |
| Rail pressure actual | `0x3B4` | broadcast |
| Rail pressure target | DDE | broadcast, byte TBD |
| Fuel consumption | `0x3B4` | broadcast |
| Gear, trans temp | `0x0BA` | broadcast |
| Vehicle speed | `0x1A0` | broadcast |
| Torque | `0x0A8` | broadcast |
| Fault codes | OBD-II | on-demand |
| EGT (factory) | OBD-II | DPF cars, post-turbo |
| EGT (pre-turbine) | — | add-on thermocouple required |
