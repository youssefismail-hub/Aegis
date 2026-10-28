import unittest
from datetime import datetime, timedelta

from consumption import FuelReading, estimate_consumption_l_per_100km


def reading(minutes, percent):
    return FuelReading(time=datetime(2026, 1, 1, 12, 0, 0) + timedelta(minutes=minutes), percent=percent)


class TestConsumptionEstimate(unittest.TestCase):
    def test_normal_trip_estimate(self):
        # 60% -> 55% of a 50 L tank = 2.5 L over 50 km -> 5.0 L/100km
        readings = [reading(0, 60.0), reading(30, 55.0)]
        result = estimate_consumption_l_per_100km(readings, distance_km=50.0, tank_capacity_l=50.0)
        self.assertAlmostEqual(result, 5.0, places=3)

    def test_unordered_readings_are_sorted_by_time(self):
        readings = [reading(30, 55.0), reading(0, 60.0)]
        result = estimate_consumption_l_per_100km(readings, distance_km=50.0, tank_capacity_l=50.0)
        self.assertAlmostEqual(result, 5.0, places=3)

    def test_refuel_returns_none(self):
        readings = [reading(0, 20.0), reading(30, 90.0)]
        self.assertIsNone(estimate_consumption_l_per_100km(readings, distance_km=50.0))

    def test_short_distance_returns_none(self):
        readings = [reading(0, 60.0), reading(2, 59.0)]
        self.assertIsNone(estimate_consumption_l_per_100km(readings, distance_km=1.0))

    def test_fewer_than_two_readings_returns_none(self):
        self.assertIsNone(estimate_consumption_l_per_100km([reading(0, 60.0)], distance_km=50.0))
        self.assertIsNone(estimate_consumption_l_per_100km([], distance_km=50.0))

    def test_no_fuel_change_returns_none(self):
        readings = [reading(0, 60.0), reading(30, 60.0)]
        self.assertIsNone(estimate_consumption_l_per_100km(readings, distance_km=50.0))


if __name__ == "__main__":
    unittest.main()