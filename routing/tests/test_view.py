"""End-to-end view tests with OSRM + endpoint geocoding mocked."""

from unittest import mock

import numpy as np
from django.test import SimpleTestCase

from routing.services import geo
from routing.tests.test_geo import straight_route


class RouteViewTests(SimpleTestCase):
    """Tests for the public /route/ API endpoint."""

    def setUp(self):
        """Provide a small in-memory fuel-station dataset for each test."""
        geo._STATIONS = {
            "lat": np.array([40.0, 40.0]),
            "lng": np.array([-99.0, -95.0]),
            "price": np.array([3.0, 2.5]),
            "meta": [
                {
                    "name": "first",
                    "city": "A",
                    "state": "XX",
                },
                {
                    "name": "second",
                    "city": "B",
                    "state": "XX",
                },
            ],
        }

    def tearDown(self):
        """Clear the station cache after each test."""
        geo.clear_cache()

    def _patched(self, distance):
        """Mock endpoint resolution and OSRM routing."""
        coords = straight_route(
            40.0,
            -100.0,
            -90.0,
        )

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
        """A valid request returns the expected response structure."""
        p_resolve, p_route = self._patched(530.0)

        with p_resolve, p_route:
            response = self.client.get(
                "/route/",
                {
                    "start": "start",
                    "finish": "finish",
                },
            )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        # --------------------------------------------------------------
        # Route
        # --------------------------------------------------------------
        self.assertEqual(
            data["route"]["type"],
            "LineString",
        )

        self.assertEqual(
            data["distance_miles"],
            530.0,
        )

        self.assertIn(
            "coordinates",
            data["route"],
        )

        self.assertIsInstance(
            data["route"]["coordinates"],
            list,
        )

        # --------------------------------------------------------------
        # Total fuel cost
        # --------------------------------------------------------------
        self.assertIn(
            "total_fuel_cost_usd",
            data,
        )

        self.assertIsInstance(
            data["total_fuel_cost_usd"],
            (int, float),
        )

        self.assertGreaterEqual(
            data["total_fuel_cost_usd"],
            0,
        )

        # The vehicle starts with a full tank, so the API must NOT add
        # a separate starting-fuel cost.
        self.assertNotIn(
            "starting_fuel_cost_usd",
            data,
        )

        # --------------------------------------------------------------
        # Fuel stops
        # --------------------------------------------------------------
        self.assertIn(
            "fuel_stops",
            data,
        )

        self.assertIsInstance(
            data["fuel_stops"],
            list,
        )

        self.assertGreater(
            len(data["fuel_stops"]),
            0,
        )

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

            self.assertGreaterEqual(
                stop["gallons"],
                0,
            )

            self.assertGreaterEqual(
                stop["cost_usd"],
                0,
            )

            self.assertGreater(
                stop["price_per_gallon"],
                0,
            )

        # --------------------------------------------------------------
        # Vehicle configuration
        # --------------------------------------------------------------
        self.assertIn(
            "meta",
            data,
        )

        self.assertEqual(
            data["meta"]["vehicle_range_miles"],
            500.0,
        )

        self.assertEqual(
            data["meta"]["vehicle_mpg"],
            10.0,
        )

        # 500 miles / 10 MPG = 50 gallons.
        tank_gallons = (
            data["meta"]["vehicle_range_miles"]
            / data["meta"]["vehicle_mpg"]
        )

        self.assertEqual(
            tank_gallons,
            50.0,
        )

        self.assertIn(
            "elapsed_ms",
            data["meta"],
        )

        self.assertGreaterEqual(
            data["meta"]["elapsed_ms"],
            0,
        )

    def test_total_cost_equals_fuel_stop_costs(self):
        """Total API cost equals the sum of actual fuel purchases."""
        p_resolve, p_route = self._patched(530.0)

        with p_resolve, p_route:
            response = self.client.get(
                "/route/",
                {
                    "start": "start",
                    "finish": "finish",
                },
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        expected_total = round(
            sum(
                stop["cost_usd"]
                for stop in data["fuel_stops"]
            ),
            2,
        )

        self.assertEqual(
            data["total_fuel_cost_usd"],
            expected_total,
        )

    def test_starting_fuel_is_not_charged_again(self):
        """The initial full tank is not added to the reported trip cost."""
        p_resolve, p_route = self._patched(530.0)

        with p_resolve, p_route:
            response = self.client.get(
                "/route/",
                {
                    "start": "start",
                    "finish": "finish",
                },
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        # At 10 MPG, a 500-mile range corresponds to a 50-gallon tank.
        starting_tank_gallons = (
            data["meta"]["vehicle_range_miles"]
            / data["meta"]["vehicle_mpg"]
        )

        self.assertEqual(
            starting_tank_gallons,
            50.0,
        )

        # The initial tank itself is not represented as a fuel stop.
        # Every reported gallon must therefore be an actual purchase.
        purchased_gallons = round(
            sum(
                stop["gallons"]
                for stop in data["fuel_stops"]
            ),
            2,
        )

        self.assertGreater(
            purchased_gallons,
            0,
        )

        # The API total is based only on these purchases.
        expected_total = round(
            sum(
                stop["cost_usd"]
                for stop in data["fuel_stops"]
            ),
            2,
        )

        self.assertEqual(
            data["total_fuel_cost_usd"],
            expected_total,
        )

        self.assertNotIn(
            "starting_fuel_cost_usd",
            data,
        )

    def test_infeasible_returns_422(self):
        """A route with an unreachable fuel gap returns HTTP 422."""
        p_resolve, p_route = self._patched(1400.0)

        with p_resolve, p_route:
            response = self.client.get(
                "/route/",
                {
                    "start": "start",
                    "finish": "finish",
                },
            )

        self.assertEqual(
            response.status_code,
            422,
        )

        self.assertIn(
            "error",
            response.json(),
        )

        self.assertIn(
            "distance_miles",
            response.json(),
        )

    def test_bad_input_returns_400(self):
        """Unresolvable start/finish locations return HTTP 400."""
        from routing.services.resolve import ResolveError

        with mock.patch(
            "routing.views.resolve",
            side_effect=ResolveError("nope"),
        ):
            response = self.client.get(
                "/route/",
                {
                    "start": "",
                    "finish": "",
                },
            )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "error",
            response.json(),
        )

    def test_routing_service_unavailable_returns_502(self):
        """An unavailable OSRM service returns HTTP 502."""
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
            side_effect=RouteServiceError(
                "OSRM unavailable"
            ),
        ):
            response = self.client.get(
                "/route/",
                {
                    "start": "start",
                    "finish": "finish",
                },
            )

        self.assertEqual(
            response.status_code,
            502,
        )

        self.assertEqual(
            response.json()["error"],
            "Routing service unavailable.",
        )

    def test_geometry_defaults_to_simplified(self):
        """Default geometry is the display-downsampled route."""
        p_resolve, p_route = self._patched(530.0)

        with p_resolve, p_route:
            response = self.client.get(
                "/route/",
                {
                    "start": "start",
                    "finish": "finish",
                },
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["meta"]["geometry"],
            "simplified",
        )

        self.assertEqual(
            data["meta"]["route_points"],
            len(data["route"]["coordinates"]),
        )

    def test_full_geometry_option(self):
        """geometry=full returns the complete mocked route."""
        p_resolve, p_route = self._patched(530.0)

        with p_resolve, p_route:
            response = self.client.get(
                "/route/",
                {
                    "start": "start",
                    "finish": "finish",
                    "geometry": "full",
                },
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["meta"]["geometry"],
            "full",
        )

        self.assertEqual(
            data["meta"]["route_points"],
            len(data["route"]["coordinates"]),
        )