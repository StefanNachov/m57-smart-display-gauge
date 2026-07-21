"""Per-CAN-ID decode functions. Each returns a dict of ECUData field updates.

Byte offsets/scales validated on-vehicle during commissioning (see docs/CAN_MAP.md).
"""

def decode_0AA(d):
    if len(d) < 4: return {}
    return {"rpm": int(((d[0] << 8) | d[1]) * 0.25),
            "pedal_pct": round(d[2] * 0.392, 1)}

def decode_1D0(d):
    if len(d) < 8: return {}
    return {"coolant_c": d[1] - 48,
            "iat_c": d[3] - 48,
            "boost_actual_bar": round(d[4] * 0.01, 2),
            "boost_target_bar": round(d[5] * 0.01, 2)}

def decode_1B6(d):
    if len(d) < 4: return {}
    return {"oil_c": d[2] - 48}

def decode_0BA(d):
    if len(d) < 6: return {}
    gears = {0: "P", 1: "R", 2: "N", 3: "D", 4: "1",
             5: "2", 6: "3", 7: "4", 8: "5", 9: "6"}
    return {"gear": gears.get(d[0] & 0x0F, "?"), "trans_c": d[5] - 48}

def decode_1A0(d):
    if len(d) < 2: return {}
    return {"speed_kph": round(((d[0] << 8) | d[1]) * 0.01, 1)}

def decode_3B4(d):
    if len(d) < 6: return {}
    return {"rail_actual_bar": round(((d[0] << 8) | d[1]) * 0.1, 0),
            "fuel_lph": round(d[4] * 0.1, 1)}

def decode_0A8(d):
    if len(d) < 3: return {}
    return {"torque_nm": int(((d[2] << 8) | d[1]) * 0.03125)}

DECODERS = {
    0x0AA: decode_0AA, 0x1D0: decode_1D0, 0x1B6: decode_1B6,
    0x0BA: decode_0BA, 0x1A0: decode_1A0, 0x3B4: decode_3B4,
    0x0A8: decode_0A8,
}
