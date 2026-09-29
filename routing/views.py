"""The one read endpoint. The view only parses, orchestrates, and serializes;
every piece of logic lives in tested services.

Contract:
    GET /route/?start=<place|lat,lng>&finish=<place|lat,lng>

Status codes:
    200  route found
    400  start/finish missing or unresolvable
    422  no drivable route, or route infeasible for the 500-mile tank range
    502  the routing service (OSRM) was unreachable
"""

import time

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from routing.services import geo
from routing.services.fuel import Infeasible, plan_fuel
from routing.services.osrm import RouteError, RouteServiceError, get_route
from routing.services.resolve import ResolveError, resolve


# Default cap on polyline points returned to the client.
# Full geometry can contain tens of thousands of points, so this keeps the
# response payload small and the map smooth.
#
# IMPORTANT:
# This is DISPLAY ONLY. The fuel plan is calculated using the full route
# geometry, so downsampling does not affect the fuel-stop calculation.
# Use ?geometry=full to return every route vertex.
_DISPLAY_MAX_POINTS = 600


def _downsample_for_display(coords, max_points=_DISPLAY_MAX_POINTS):
    """Evenly thin the polyline to at most ``max_points`` points.

    The first and last coordinates are always preserved.
    """
    n = len(coords)

    if n <= max_points:
        return coords

    step = (n - 1) / (max_points - 1)

    idx = sorted(
        {round(i * step) for i in range(max_points)}
        | {0, n - 1}
    )

    return [coords[i] for i in idx]


def _serialize_stop(s):
    """Map an internal fuel-stop dict to the public JSON shape.

    Internal keys:
        mile  -> mile_marker
        price -> price_per_gallon

    Values are rounded to keep the API response compact and readable.
    """
    return {
        "name": s["name"],
        "city": s["city"],
        "state": s["state"],
        "lat": round(s["lat"], 5),
        "lng": round(s["lng"], 5),
        "price_per_gallon": round(s["price"], 4),
        "gallons": s["gallons"],
        "cost_usd": s["cost_usd"],
        "mile_marker": round(s["mile"], 1),
    }


@require_GET
def route_view(request):
    """Return the driving route and cost-effective fuel stops.

    The vehicle leaves the origin with a full tank.

    Therefore:
        total_fuel_cost_usd

    represents only the additional fuel purchased during the journey.
    Fuel already present in the vehicle at the start is not charged again.
    """

    # Time the complete request so the API can report elapsed time.
    t0 = time.perf_counter()

    # ------------------------------------------------------------------
    # 1. Resolve start and finish locations.
    #
    # Supported forms:
    #   - "City, ST"
    #   - "lat,lng"
    # ------------------------------------------------------------------
    try:
        start = resolve(request.GET.get("start", ""))
        finish = resolve(request.GET.get("finish", ""))
    except ResolveError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

    # ------------------------------------------------------------------
    # 2. Get the driving route.
    #
    # This is the single external routing call made during the request.
    # The OSRM service itself is cached by the routing service.
    # ------------------------------------------------------------------
    try:
        coords, distance_mi = get_route(start, finish)

    except RouteError as exc:
        # OSRM responded but could not find a drivable route.
        return JsonResponse(
            {"error": str(exc)},
            status=422,
        )

    except RouteServiceError:
        # OSRM itself was unreachable or returned an unexpected service error.
        return JsonResponse(
            {"error": "Routing service unavailable."},
            status=502,
        )

    # ------------------------------------------------------------------
    # 3. Find fuel stations along the route.
    #
    # This is performed locally using the supplied fuel-price data and
    # spatial filtering. No external fuel-station API is called here.
    # ------------------------------------------------------------------
    candidates = geo.stations_along_route(
        coords,
        distance_mi,
    )

    # ------------------------------------------------------------------
    # 4. Calculate the optimal fuel purchases.
    #
    # plan_fuel() assumes the vehicle starts with a full tank and returns:
    #
    #   total = cost of additional fuel purchased during the trip
    #   stops = ordered fuel purchases
    #
    # It also raises Infeasible when a route leg exceeds the vehicle's
    # maximum range without a reachable fuel station.
    # ------------------------------------------------------------------
    try:
        total, stops = plan_fuel(
            candidates,
            distance_mi,
        )

    except Infeasible as exc:
        return JsonResponse(
            {
                "error": str(exc),
                "distance_miles": round(distance_mi, 1),
            },
            status=422,
        )

    # ------------------------------------------------------------------
    # 5. Prepare route geometry for the response.
    #
    # Default:
    #   simplified geometry with at most 600 points.
    #
    # Optional:
    #   ?geometry=full
    #
    # IMPORTANT:
    # This only affects the returned/displayed geometry.
    # It does NOT affect the fuel calculation.
    # ------------------------------------------------------------------
    want_full = request.GET.get("geometry") == "full"

    route_coords = (
        coords
        if want_full
        else _downsample_for_display(coords)
    )

    # ------------------------------------------------------------------
    # 6. Calculate request duration.
    # ------------------------------------------------------------------
    elapsed_ms = (
        time.perf_counter() - t0
    ) * 1000.0

    # ------------------------------------------------------------------
    # 7. Return the API response.
    # ------------------------------------------------------------------
    return JsonResponse(
        {
            "route": {
                "type": "LineString",
                "coordinates": route_coords,
            },
            "distance_miles": round(
                distance_mi,
                1,
            ),
            "total_fuel_cost_usd": total,
            "fuel_stops": [
                _serialize_stop(s)
                for s in stops
            ],
            "meta": {
                "stations_considered": len(candidates),
                "route_points": len(route_coords),
                "geometry": (
                    "full"
                    if want_full
                    else "simplified"
                ),
                "corridor_miles": settings.CORRIDOR_MILES,
                "vehicle_range_miles": (
                    settings.VEHICLE_RANGE_MILES
                ),
                "vehicle_mpg": settings.VEHICLE_MPG,
                "elapsed_ms": round(
                    elapsed_ms,
                    1,
                ),
            },
        }
    )


def map_view(request):
    """Serve the Leaflet demo page that fetches /route and draws it."""
    return render(
        request,
        "routing/map.html",
        {
            "carto_key": settings.CARTO_KEY,
        },
    )


def _api_spec():
    """Machine-readable description of the API.

    The specification is built from live Django settings so documented
    vehicle limits remain aligned with the actual application configuration.
    """
    return {
        "name": "Fuel Route API",
        "description": (
            "Given a start and finish in the USA, returns the driving route, "
            "the cost-optimal fuel stops along it, and the total fuel cost."
        ),
        "endpoints": {
            "GET /route/": {
                "summary": "Plan a fuelling route.",
                "query_params": {
                    "start": (
                        "Required. 'lat,lng' or a place name "
                        "(e.g. 'Dallas, TX')."
                    ),
                    "finish": (
                        "Required. 'lat,lng' or a place name."
                    ),
                    "geometry": (
                        "Optional. 'simplified' (default, small payload) "
                        "or 'full'."
                    ),
                },
                "returns": (
                    "route GeoJSON, ordered fuel_stops, "
                    "total_fuel_cost_usd, meta"
                ),
                "status_codes": {
                    "200": "route found",
                    "400": (
                        "start/finish missing or unresolvable"
                    ),
                    "422": (
                        "no drivable route, or infeasible "
                        "for the tank range"
                    ),
                    "502": (
                        "routing service (OSRM) unreachable"
                    ),
                },
                "examples": [
                    (
                        "/route/?start=Los Angeles, CA"
                        "&finish=New York, NY"
                    ),
                    (
                        "/route/?start=34.05,-118.24"
                        "&finish=40.71,-74.01"
                    ),
                ],
            },
            "GET /map/": {
                "summary": "Interactive Leaflet demo page.",
            },
            "GET /api/": {
                "summary": (
                    "This machine-readable API spec (JSON)."
                ),
            },
            "GET /": {
                "summary": (
                    "Human-readable API documentation (HTML)."
                ),
            },
        },
        "vehicle_model": {
            "range_miles": settings.VEHICLE_RANGE_MILES,
            "mpg": settings.VEHICLE_MPG,
            "tank_gallons": (
                settings.VEHICLE_RANGE_MILES
                / settings.VEHICLE_MPG
            ),
            "corridor_miles": settings.CORRIDOR_MILES,
            "assumption": (
                "Vehicle leaves the origin with a full tank; "
                "total_fuel_cost_usd includes only fuel purchased "
                "during the journey."
            ),
        },
    }


def api_spec_view(request):
    """Return the API specification as JSON."""
    return JsonResponse(
        _api_spec()
    )


def docs_view(request):
    """Render the human-readable API documentation page."""
    return render(
        request,
        "routing/docs.html",
        {
            "spec": _api_spec(),
        },
    )

