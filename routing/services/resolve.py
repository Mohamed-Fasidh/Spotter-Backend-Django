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

# Approximate bounding boxes: (min_lat, max_lat, min_lng, max_lng).
# Rough by design: catches obvious non-US points, but border areas of
# Canada/Mexico that fall inside a box are not rejected.
_US_BOXES = [
    (24.4, 49.5, -125.0, -66.9),    # contiguous US
    (51.2, 71.5, -180.0, -129.9),   # Alaska
    (18.8, 22.5, -160.6, -154.7),   # Hawaii
]


def _in_usa(lat, lng):
    return any(a <= lat <= b and c <= lng <= d for a, b, c, d in _US_BOXES)


def resolve(value: str):
    """Return (lat, lng) for a start/finish string."""

    # 1. Basic input validation
    if not value or not value.strip():
        raise ResolveError("Missing start/finish value.")

    value = value.strip()

    # 2. Direct lat,lng input (e.g. "34.0522,-118.2437"); no lookups needed.
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

    # 3. Offline "City, ST" lookup against the bundled US city table.
    if "," in value:
        city, _, tail = value.rpartition(",")
        state = tail.strip().upper()

        if len(state) == 2 and state.isalpha():
            coord = cities.lookup(city.strip(), state)

            if coord is not None:
                return coord

    # 4. Anything else is rejected rather than guessed.
    raise ResolveError(
        f"Could not find a US location for {value!r}. "
        "Use 'City, ST' (e.g. 'Dallas, TX') or 'lat,lng'."
    )