import unittest
from datetime import datetime, timedelta

from trips import SpeedReading, group_into_trips, TRIP_GAP_SECONDS


def dt(seconds_offset):
    return datetime(2026, 1, 1, 12, 0, 0) + timedelta(seconds=seconds_offset)


class TestTripGrouping(unittest.TestCase):
    def test_empty_readings_returns_no_trips(self):
        self.assertEqual(group_into_trips([]), [])

    def test_single_reading_is_one_trip_with_zero_duration_and_distance(self):
        trips = group_into_trips([SpeedReading(time=dt(0), value=50.0)])
        self.assertEqual(len(trips), 1)
        self.assertEqual(trips[0].duration_seconds, 0)
        self.assertEqual(trips[0].distance_km, 0)

    def test_close_readings_grouped_into_one_trip(self):
        readings = [
            SpeedReading(time=dt(0), value=0.0),
            SpeedReading(time=dt(10), value=50.0),
            SpeedReading(time=dt(20), value=60.0),
        ]
        trips = group_into_trips(readings, gap_seconds=7200)  # override: this test spans 1hr between just 2 points
        self.assertEqual(len(trips), 1)
        self.assertEqual(trips[0].max_speed_kmh, 60.0)

    def test_large_gap_splits_into_two_separate_trips(self):
        readings = [
            SpeedReading(time=dt(0), value=50.0),
            SpeedReading(time=dt(10), value=55.0),
            SpeedReading(time=dt(10 + TRIP_GAP_SECONDS + 60), value=30.0),
        ]
        trips = group_into_trips(readings)
        self.assertEqual(len(trips), 2)
        self.assertEqual(trips[0].max_speed_kmh, 55.0)
        self.assertEqual(trips[1].max_speed_kmh, 30.0)

    def test_distance_via_trapezoidal_integration(self):
        # Constant 60 km/h for exactly 1 hour -> exactly 60 km.
        readings = [
            SpeedReading(time=dt(0), value=60.0),
            SpeedReading(time=dt(3600), value=60.0),
        ]
        trips = group_into_trips(readings, gap_seconds=7200)  # override: this test spans 1hr between just 2 points
        self.assertAlmostEqual(trips[0].distance_km, 60.0, places=3)


if __name__ == "__main__":
    unittest.main()