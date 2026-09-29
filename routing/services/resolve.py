"""Resolve the two endpoints (start/finish) to coordinates.

Accepts either:

  - "lat,lng" -> parsed directly and checked to be inside the USA; or
  - "City, ST" -> looked up in the bundled offline US city table.

There is deliberately NO external geocoding: it keeps requests fast, uses
zero geocoder calls, and avoids silently guessing a wrong place for
ambiguous input such as "London" or "Toronto, Canada".

Stations are never geocoded at request time either.
"""

import re

from routing.services import cities


class ResolveError(Exception):
    """The start/finish value could not be turned into coordinates."""


_LATLNG_RE = re.compile(
    r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$"
)

# Local, dependency-free boundary polygons used to reject non-US coordinate
# inputs without making an external geocoding/API call.
# Coordinates are stored as (longitude, latitude).
_US_POLYGONS = (
    (
        # Contiguous United States (simplified outer boundary).
        (-124.75, 48.42), (-123.00, 46.00), (-124.20, 42.00),
        (-122.50, 38.00), (-120.00, 35.00), (-117.10, 32.53),
        (-114.72, 32.72), (-111.02, 31.33), (-106.51, 31.75),
        (-104.46, 29.57), (-99.30, 26.84), (-97.14, 25.87),
        (-95.00, 29.00), (-90.00, 29.10), (-87.50, 30.27),
        (-84.10, 30.09), (-81.00, 25.20), (-80.00, 26.20),
        (-80.03, 30.70), (-75.70, 35.55), (-74.00, 40.40),
        (-70.60, 41.50), (-67.79, 45.14), (-71.50, 45.01),
        (-74.90, 45.00), (-79.00, 43.00), (-83.00, 42.00),
        (-84.80, 46.90), (-90.80, 48.00), (-95.16, 49.00),
        (-100.65, 49.00), (-107.05, 49.00), (-113.00, 49.00),
        (-117.03, 49.00), (-120.00, 49.00), (-124.75, 48.42),
    ),
    (
        # Alaska (simplified outer boundary).
        (-168.00, 54.40), (-160.00, 55.60), (-153.00, 57.10),
        (-148.00, 59.98), (-141.00, 60.31), (-140.99, 66.00),
        (-140.99, 70.00), (-155.07, 71.15), (-166.85, 65.09),
        (-171.73, 63.78), (-168.00, 54.40),
    ),
    (
        # Hawaii envelope. The existing city lookup remains the authoritative
        # path for City, ST input; this supports direct Hawaii coordinates.
        (-160.30, 18.80), (-154.70, 18.80),
        (-154.70, 22.30), (-160.30, 22.30),
        (-160.30, 18.80),
    ),
)


def _point_in_polygon(lng, lat, polygon):
    """Return True when a point is inside a polygon using ray casting."""
    inside = False
    j = len(polygon) - 1

    for i, (x_i, y_i) in enumerate(polygon):
        x_j, y_j = polygon[j]

        intersects = ((y_i > lat) != (y_j > lat)) and (
            lng < (x_j - x_i) * (lat - y_i) / (y_j - y_i) + x_i
        )

        if intersects:
            inside = not inside

        j = i

    return inside


def _in_usa(lat, lng):
    """Return True when the coordinate is inside a local US polygon."""
    return any(
        _point_in_polygon(lng, lat, polygon)
        for polygon in _US_POLYGONS
    )


def resolve(value: str):
    """Return (lat, lng) for a start/finish string."""

    if not value or not value.strip():
        raise ResolveError("Missing start/finish value.")

    value = value.strip()

    # Direct lat,lng input; no external lookup.
    match = _LATLNG_RE.match(value)

    if match:
        lat = float(match.group(1))
        lng = float(match.group(2))

        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ResolveError(f"Coordinates out of range: {value!r}")

        if not _in_usa(lat, lng):
            raise ResolveError(
                f"Location must be within the United States: {value!r}"
            )

        return lat, lng

    # Offline "City, ST" lookup against the bundled US city table.
    if "," in value:
        city, _, tail = value.rpartition(",")
        state = tail.strip().upper()

        if len(state) == 2 and state.isalpha():
            coord = cities.lookup(city.strip(), state)

            if coord is not None:
                return coord

    raise ResolveError(
        f"Could not find a US location for {value!r}. "
        "Use 'City, ST' (e.g. 'Dallas, TX') or 'lat,lng'."
    )