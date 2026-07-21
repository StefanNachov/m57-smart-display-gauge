# Engineering Notes

Design decisions, trade-offs, and debugging history. This document exists
because the *why* behind a hardware project is often more instructive than the
final wiring diagram — and several of these problems took real diagnostic work
to isolate.

---

## 1. Choosing a CAN transceiver: TJA1050 vs SN65HVD230

**Symptom.** With a common blue MCP2515 + TJA1050 module, the CAN controller
would initialise correctly and pass an internal loopback self-test, yet receive
zero frames from a confirmed-live vehicle bus. The controller's receive error
counter stayed at zero — meaning it perceived a completely idle line — while the
physical bus was measurably active (60 Ω termination present, ~2.5 V common
mode).

**Diagnosis.** Loopback exercises the controller and SPI path but bypasses the
transceiver entirely. A passing loopback with no bus reception isolates the
fault to the transceiver or its board-level connection. The root cause is a
design compromise in cheap combined boards: the MCP2515 controller must run at
3.3 V (its SPI lines connect to the Pi's 3.3 V GPIO), while the CAN bus side
wants 5 V levels. Single-rail boards tie both chips together, forcing a
compromise voltage. At 3.3 V the transceiver is under-driven; ground-reference
offsets push the differential outside its detection window, and it fails to
deliver received bits to the controller despite biasing the lines correctly.

**Resolution.** The SN65HVD230 is a native 3.3 V transceiver. Controller,
transceiver, and Pi share one voltage domain and one ground reference, removing
the conflict. Purpose-built Pi CAN HATs use this part for exactly this reason.

**Takeaway.** A component that "powers up and self-tests" is not proven
functional in-circuit. Loopback proved the digital half; only a bus-level test
could exercise the analog half. Choosing the right part up front — matched to
the system's voltage domain — would have avoided the entire investigation.

---

## 2. Power integrity on a vehicle supply

**Symptom.** Intermittent SPI failures and dropped communication with the CAN
controller, correlating with the Pi logging under-voltage events.

**Diagnosis.** The Raspberry Pi trips an under-voltage warning at ~4.63 V. A
5.0 V nominal supply, after cable and connector losses, can idle around
4.85–4.9 V and dip below the threshold under transient load — during which SPI
timing degrades and the CAN controller can drop out mid-transaction. The failure
was consistently a power artefact, not a logic or wiring fault.

**Resolution.** Regulate to **5.1 V** (the value the official Pi supply targets
for the same reason) to provide headroom above the threshold. Confirm with
`vcgencmd get_throttled` returning `0x0`, and prefer a supply/cable that
maintains voltage under load. USB-PD chargers negotiate and hold voltage far
better than passive 5 V sources.

**Takeaway.** On embedded systems, "it boots" is not "it has adequate power."
Marginal supplies fail intermittently under load in ways that masquerade as
logic bugs.

---

## 3. Oscillator/crystal mismatch

**Symptom.** After bring-up, `can0` came up cleanly and reported no errors, but
received nothing.

**Diagnosis.** The MCP2515 device-tree overlay specifies the crystal frequency
(`oscillator=`). If this does not match the physical crystal (8 MHz on many bare
modules, 12 MHz on the Waveshare HAT used here), the controller's bit-timing is
wrong and it cannot frame the incoming 500 kbps traffic — producing a silent,
error-free interface. Verified via
`ip -details link show can0 | grep clock`.

**Resolution.** Set `oscillator=` to match the board's crystal exactly.

**Takeaway.** A silent interface with zero error counters is a signature of a
bit-timing/clock mismatch, distinct from a wiring or polarity fault (which
increments error counters as the controller tries and fails to decode activity).

---

## 4. Identifying the correct bus wires

**Symptom.** A tapped twisted pair measured plausibly but carried no traffic.

**Diagnosis.** A CAN pair is identifiable by its ~60 Ω termination signature
(two 120 Ω terminators in parallel) measured across the pair with the ignition
off. DC voltage on individual lines is a poor discriminator — a multimeter shows
only the time-average, which sits near common mode regardless of activity.
Confirming ~60 Ω on the pair, and confirming the connector was fully seated,
were both necessary.

**Takeaway.** Verify the bus by its termination resistance, not by per-line DC
voltage. Received frames are the ultimate ground truth; instrument readings only
narrow the search.

---

## 5. Listen-only mode as a safety default

The CAN controller is placed in **listen-only** mode for all live monitoring. In
this mode it cannot assert dominant bits or acknowledge frames — it is
electrically incapable of transmitting. This guarantees the gauge cannot disturb
the vehicle bus, which is essential for a device tapped into a safety-relevant
network. Active requests (for fault codes) are performed only in explicit,
bounded windows, and are suppressed entirely during diagnostic isolation.

---

## 6. Hardware diagnostic isolation

During an ECU remap, the flashing tool writes firmware to the DME/DDE over the
same CAN bus. If the gauge were to glitch or reset during this window, it could
corrupt the bus and the firmware write. A software "diagnostic mode" flag is
insufficient because it depends on the software continuing to run correctly.

The design uses a **GPIO-controlled relay** that physically opens the CAN H/L
lines between the tap and the transceiver. With the relay open, the gauge has
zero electrical presence on the bus regardless of software state — the only
guaranteed-safe condition for flashing.

---

## 7. Deviation-based alerting

Absolute thresholds (e.g. "warn if boost > X") do not generalise across states
of tune. Because the ECU broadcasts both actual and commanded-target values for
boost (and rail pressure), the alert engine compares the two and alerts on
**deviation**. This makes the same firmware correct for a stock car and a
heavily-modified one, with only the display's full-scale range needing
per-vehicle configuration. It also produces a more meaningful alert: a boost
value that is "high" in absolute terms is fine if the ECU commanded it, whereas a
small shortfall against target can indicate a developing fault.
