"""
Fuel consumption ESTIMATE from fuel-level readings (PID 0x2F, percent).

Honest limitations, stated up front because this is easy to oversell:
- Fuel level sensors are noisy (fuel sloshes) and coarse, so short trips
  give meaningless results. Below MIN_DISTANCE_KM we return None
  instead of a misleading number.
- Tank capacity is an assumption (a parameter, defaulting to 50 L),
  not something OBD-II reports.
- A rising fuel level means a refuel happened mid-window, so we cannot
  estimate and return None.
- Real consumption modeling would use MAF/injector data. This is a
  level-delta estimate only.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

MIN_DISTANCE_KM = 5.0
DEFAULT_TANK_CAPACITY_L = 50.0


@dataclass
class FuelReading:
    time: datetime
    percent: float


def estimate_consumption_l_per_100km(
    fuel_readings: List[FuelReading],
    distance_km: float,
    tank_capacity_l: float = DEFAULT_TANK_CAPACITY_L,
) -> Optional[float]:
    """Returns estimated L/100km, or None when an honest estimate isn't possible."""
    if len(fuel_readings) < 2:
        return None
    if distance_km < MIN_DISTANCE_KM:
        return None

    ordered = sorted(fuel_readings, key=lambda r: r.time)
    used_percent = ordered[0].percent - ordered[-1].percent

    if used_percent <= 0:
        return None  # refuel or sensor noise, no valid estimate

    litres_used = (used_percent / 100.0) * tank_capacity_l
    return litres_used / distance_km * 100.0