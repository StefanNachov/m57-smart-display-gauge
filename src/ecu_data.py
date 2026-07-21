"""Shared ECU state model — populated by decoders, read by display/alerts/logger."""
from dataclasses import dataclass, field
from time import time


@dataclass
class ECUData:
    # engine
    rpm: int = 0
    pedal_pct: float = 0.0
    boost_actual_bar: float = 0.0
    boost_target_bar: float = 0.0
    coolant_c: int = 0
    iat_c: int = 0
    oil_c: int = 0
    rail_actual_bar: float = 0.0
    rail_target_bar: float | None = None   # None until byte confirmed
    fuel_lph: float = 0.0
    torque_nm: int = 0
    # drivetrain
    gear: str = "?"
    trans_c: int = 0
    tcc_lockup_pct: float = 0.0
    speed_kph: float = 0.0
    # optional add-on sensors
    oil_pressure_bar: float | None = None
    egt_c: float | None = None
    # bookkeeping
    last_update: float = field(default_factory=time)

    def touch(self):
        self.last_update = time()
