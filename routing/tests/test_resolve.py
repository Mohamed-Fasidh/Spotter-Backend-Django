"""Endpoint resolution tests."""

from django.test import SimpleTestCase

from routing.services import resolve


class ResolveTests(SimpleTestCase):
    def test_parses_lat_lng(self):
        self.assertEqual(resolve.resolve("36.12, -97.14"), (36.12, -97.14))

    def test_rejects_out_of_range(self):
        with self.assertRaises(resolve.ResolveError):
            resolve.resolve("999,999")

    def test_empty_raises(self):
        with self.assertRaises(resolve.ResolveError):
            resolve.resolve("")

    def test_city_state_uses_offline_table(self):
        lat, lng = resolve.resolve("Chicago, IL")
        self.assertAlmostEqual(lat, 41.85, delta=0.5)
        self.assertAlmostEqual(lng, -87.65, delta=0.5)

    def test_rejects_non_us_coordinates(self):
        with self.assertRaises(resolve.ResolveError):
            resolve.resolve("51.5,-0.12")  # London, England

    def test_rejects_canada_coordinate(self):
        with self.assertRaises(resolve.ResolveError):
            resolve.resolve("49.3,-100.0")  # Canada

    def test_rejects_mexico_coordinate(self):
        with self.assertRaises(resolve.ResolveError):
            resolve.resolve("25.0,-100.0")  # Mexico

    def test_accepts_alaska_and_hawaii_coordinates(self):
        self.assertEqual(resolve.resolve("64.8,-147.7"), (64.8, -147.7))
        self.assertEqual(resolve.resolve("21.3,-157.8"), (21.3, -157.8))

    def test_rejects_place_without_state(self):
        with self.assertRaises(resolve.ResolveError):
            resolve.resolve("London")
        with self.assertRaises(resolve.ResolveError):
            resolve.resolve("Toronto,Canada")

    def test_city_with_state_disambiguates(self):
        lat, lng = resolve.resolve("London, KY")
        self.assertAlmostEqual(lat, 37.13, delta=0.5)
        self.assertAlmostEqual(lng, -84.08, delta=0.5)
