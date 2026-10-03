"""
Trip-detection logic: groups a stream of speed readings into discrete
trips based on time gaps, and estimates distance via trapezoidal
integration of speed over time. Deliberately has zero database
dependency — testable with plain Python objects, see test_trips.py.

Honest limitation: a real trip boundary is usually "ignition on/off,"
which this project doesn't have a direct signal for yet. A large gap in
speed readings is used as a proxy instead — reasonable, but not the
same thing (e.g. idling with the engine on but not moving for 6+
minutes would incorrectly look like two trips here).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

TRIP_GAP_SECONDS = 300  # 5 minutes with no speed reading ends a trip


@dataclass
class SpeedReading:
    time: datetime
    value: float


@dataclass
class Trip:
    start: datetime
    end: datetime
    duration_seconds: float
    max_speed_kmh: float
    avg_speed_kmh: float
    distance_km: float


def group_into_trips(readings: List[SpeedReading], gap_seconds: int = TRIP_GAP_SECONDS) -> List[Trip]:
    if not readings:
        return []

    trips = []
    current_group = [readings[0]]

    for prev, curr in zip(readings, readings[1:]):
        gap = (curr.time - prev.time).total_seconds()
        if gap > gap_seconds:
            trips.append(_build_trip(current_group))
            current_group = []
        current_group.append(curr)

    trips.append(_build_trip(current_group))
    return trips


def _build_trip(readings: List[SpeedReading]) -> Trip:
    start = readings[0].time
    end = readings[-1].time
    duration = (end - start).total_seconds()

    speeds = [r.value for r in readings]
    max_speed = max(speeds)
    avg_speed = sum(speeds) / len(speeds)

    # Trapezoidal integration: distance = sum of (avg speed of each
    # consecutive pair) * (time between them). Standard numerical
    # integration technique for unevenly-spaced samples — exact for a
    # linear speed profile between points, an approximation otherwise.
    distance = 0.0
    for prev, curr in zip(readings, readings[1:]):
        dt_hours = (curr.time - prev.time).total_seconds() / 3600.0
        avg_v = (prev.value + curr.value) / 2.0
        distance += avg_v * dt_hours

    return Trip(start=start, end=end, duration_seconds=duration,
                max_speed_kmh=max_speed, avg_speed_kmh=avg_speed, distance_km=distance)