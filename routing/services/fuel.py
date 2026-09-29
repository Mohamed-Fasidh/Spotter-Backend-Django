"""Fuel-stop optimizer for the route-planning API.

The vehicle starts the trip with a full tank. Fuel consumption is determined
by route distance and vehicle MPG. The optimizer determines WHERE additional
fuel should be purchased based on station prices while respecting the
vehicle's maximum range.

Assumption:
    The vehicle leaves the origin with a full tank (``tank_range`` miles of
    range). The reported fuel cost represents only additional fuel purchased
    during the trip; the initial tank is not charged by the API.

Greedy strategy:
    At each station, if a lower-priced station is reachable within the
    vehicle's range, buy only enough fuel to reach that station. Otherwise,
    buy enough fuel to cover the required distance while respecting the
    maximum tank range.

The implementation is validated against a brute-force reference in the
test suite.
"""

_EPS = 1e-9


class Infeasible(Exception):
    """A leg longer than the tank range has no station in it."""


def plan_fuel(stations, distance_mi, tank_range=None, mpg=None):
    """Return (total_cost_usd, stops).

    ``stations`` is the ordered corridor list from ``stations_along_route``.
    Each stop dict carries the station fields plus ``gallons`` and ``cost_usd``.
    Raises ``Infeasible`` if any leg (origin->first, station->station,
    last->finish) exceeds ``tank_range``.
    """
    from django.conf import settings

    if tank_range is None:
        tank_range = settings.VEHICLE_RANGE_MILES
    if mpg is None:
        mpg = settings.VEHICLE_MPG

    # Feasibility: every gap between consecutive fill opportunities must fit
    # in one tank. Origin and finish bracket the station mile markers.
    marks = [0.0] + [s["mile"] for s in stations] + [distance_mi]
    for a, b in zip(marks, marks[1:]):
        if b - a > tank_range + _EPS:
            raise Infeasible(
                f"A {b - a:.0f}-mile stretch has no fuel station within the "
                f"{tank_range:.0f}-mile range."
            )

    # Fuel is tracked in MILES OF RANGE (not gallons) because consumption is
    # linear; we convert to gallons only when recording a purchase. Start full.
    fuel = tank_range
    pos = 0.0
    stops = []

    for i, s in enumerate(stations):
        # Drive from the previous position to this station, burning fuel.
        fuel -= s["mile"] - pos
        pos = s["mile"]
        remaining = distance_mi - pos

        # If the fuel already on board reaches the finish, stop buying.
        if fuel >= remaining - _EPS:
            break

        # Look ahead for the NEAREST cheaper station within one tank. Nearest,
        # not cheapest: we only commit enough fuel to reach it, then re-decide
        # there -- deferring purchases toward ever-cheaper prices. Stations are
        # ordered by mile, so the first one past tank range ends the search.
        cheaper = None
        for t in stations[i + 1:]:
            if t["mile"] - pos > tank_range + _EPS:
                break
            if t["price"] < s["price"]:
                cheaper = t
                break

        if cheaper is not None:
            target = cheaper["mile"] - pos          # just enough to reach it
        else:
            # Nothing cheaper reachable: this is the cheapest fuel around, so
            # fill up -- but never buy more range than finishing the trip needs.
            target = min(tank_range, remaining)

        buy = target - fuel
        if buy > _EPS:  # skip zero/negative buys (already have enough on board)
            gallons = buy / mpg
            stops.append(
                {
                    **s,
                    "gallons": round(gallons, 2),
                    "cost_usd": round(gallons * s["price"], 2),
                }
            )
            fuel += buy

    total = round(sum(x["cost_usd"] for x in stops), 2)
    return total, stops
