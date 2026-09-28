"""End-to-end view tests with OSRM + endpoint geocoding mocked."""

from unittest import mock

import numpy as np
from django.test import SimpleTestCase

from routing.services import geo
from routing.tests.test_geo import straight_route


class RouteViewTests(SimpleTestCase):
    def setUp(self):
        geo._STATIONS = {
            "lat": np.array([40.0, 40.0]),
            "lng": np.array([-99.0, -95.0]),
            "price": np.array([3.0, 2.5]),
            "meta": [
                {"name": "first", "city": "A", "state": "XX"},
                {"name": "second", "city": "B", "state": "XX"},
            ],
        }

    def tearDown(self):
        geo.clear_cache()

    def _patched(self, distance):
        coords = straight_route(40.0, -100.0, -90.0)

        return (
            mock.patch(
                "routing.views.resolve",
                side_effect=lambda value: (
                    (40.0, -100.0)
                    if value == "start"
                    else (40.0, -90.0)
                ),
            ),
            mock.patch(
                "routing.views.get_route",
                return_value=(coords, distance),
            ),
        )

    def test_success_shape(self):
        p_resolve, p_route = self._patched(530.0)

        with p_resolve, p_route:
            resp = self.client.get(
                "/route/",
                {"start": "start", "finish": "finish"},
            )

        self.assertEqual(resp.status_code, 200)

        data = resp.json()

        self.assertEqual(data["route"]["type"], "LineString")
        self.assertEqual(data["distance_miles"], 530.0)

        self.assertIsInstance(
            data["total_fuel_cost_usd"],
            (int, float),
        )

        self.assertGreater(len(data["fuel_stops"]), 0)

        for stop in data["fuel_stops"]:
            self.assertIn("name", stop)
            self.assertIn("city", stop)
            self.assertIn("state", stop)
            self.assertIn("lat", stop)
            self.assertIn("lng", stop)
            self.assertIn("price_per_gallon", stop)
            self.assertIn("gallons", stop)
            self.assertIn("cost_usd", stop)
            self.assertIn("mile_marker", stop)

        self.assertEqual(
            data["meta"]["vehicle_range_miles"],
            500.0,
        )

        self.assertEqual(
            data["meta"]["vehicle_mpg"],
            10.0,
        )

        self.assertIn("elapsed_ms", data["meta"])

    def test_infeasible_returns_422(self):
        p_resolve, p_route = self._patched(1400.0)

        with p_resolve, p_route:
            resp = self.client.get(
                "/route/",
                {"start": "start", "finish": "finish"},
            )

        self.assertEqual(resp.status_code, 422)
        self.assertIn("error", resp.json())

    def test_bad_input_returns_400(self):
        from routing.services.resolve import ResolveError

        with mock.patch(
            "routing.views.resolve",
            side_effect=ResolveError("nope"),
        ):
            resp = self.client.get(
                "/route/",
                {"start": "", "finish": ""},
            )

        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.json())

    def test_routing_service_unavailable_returns_502(self):
        from routing.services.osrm import RouteServiceError

        with mock.patch(
            "routing.views.resolve",
            side_effect=lambda value: (
                (40.0, -100.0)
                if value == "start"
                else (40.0, -90.0)
            ),
        ), mock.patch(
            "routing.views.get_route",
            side_effect=RouteServiceError("OSRM unavailable"),
        ):
            resp = self.client.get(
                "/route/",
                {"start": "start", "finish": "finish"},
            )

        self.assertEqual(resp.status_code, 502)
        self.assertEqual(
            resp.json()["error"],
            "Routing service unavailable.",
        )