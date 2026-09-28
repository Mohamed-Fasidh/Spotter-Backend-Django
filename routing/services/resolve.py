"""Resolve the two endpoints (start/finish) to coordinates.

Accepts either:

  - "lat,lng" -> parsed directly, zero external calls; or

  - a place name -> resolved once, cached. We try the bundled offline city
    table first ("City, ST"); only if that misses do we fall back to
    Nominatim (free, no key).

Endpoint geocoding is a separate concern from station geocoding:
stations are never geocoded at request time.

The endpoint geocoder is restricted to the United States.
"""

import re
from functools import lru_cache

import requests
from django.conf import settings

from routing.services import cities


# Reused Session for keep-alive on the rare Nominatim fallback calls.
_SESSION = requests.Session()


class ResolveError(Exception):
    """The start/finish value could not be turned into coordinates."""


_LATLNG_RE = re.compile(
    r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$"
)


def resolve(value: str):
    """Return (lat, lng) for a start/finish string."""

    # ---------------------------------------------------------
    # 1. Basic input validation
    # ---------------------------------------------------------
    if not value or not value.strip():
        raise ResolveError("Missing start/finish value.")

    value = value.strip()

    # ---------------------------------------------------------
    # 2. Direct lat,lng input
    #
    # Example:
    #   34.0522,-118.2437
    #
    # This performs no external geocoding call.
    # ---------------------------------------------------------
    match = _LATLNG_RE.match(value)

    if match:
        lat = float(match.group(1))
        lng = float(match.group(2))

        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ResolveError(
                f"Coordinates out of range: {value!r}"
            )

        return lat, lng

    # ---------------------------------------------------------
    # 3. Offline "City, ST" lookup
    #
    # Try the bundled city table first so common US locations
    # require zero external geocoding calls.
    # ---------------------------------------------------------
    if "," in value:
        city, _, tail = value.rpartition(",")
        state = tail.strip().upper()

        if len(state) == 2 and state.isalpha():
            coord = cities.lookup(city.strip(), state)

            if coord is not None:
                return coord

    # ---------------------------------------------------------
    # 4. Nominatim fallback
    #
    # Only used when the local city table cannot resolve the
    # requested place.
    # ---------------------------------------------------------
    return _nominatim(value)


@lru_cache(maxsize=256)
def _nominatim(query: str):
    """Resolve a place name using Nominatim.

    Nominatim is explicitly restricted to US results.
    The returned result is also checked to make sure the
    geocoder actually returned a US location.
    """

    try:
        response = _SESSION.get(
            settings.NOMINATIM_URL,
            params={
                "q": query,
                "format": "json",
                "limit": 1,
                "countrycodes": "us",
                "addressdetails": 1,
            },
            headers={
                "User-Agent": settings.GEOCODER_USER_AGENT
            },
            timeout=settings.EXTERNAL_HTTP_TIMEOUT,
        )

        response.raise_for_status()
        results = response.json()

    except requests.RequestException as exc:
        raise ResolveError(
            f"Geocoding service unavailable: {exc}"
        ) from exc

    # ---------------------------------------------------------
    # No result
    # ---------------------------------------------------------
    if not results:
        raise ResolveError(
            f"Could not geocode location: {query!r}"
        )

    result = results[0]

    # ---------------------------------------------------------
    # Explicitly verify the returned country.
    #
    # This is an additional defensive check even though the
    # Nominatim request already uses countrycodes=us.
    # ---------------------------------------------------------
    address = result.get("address", {})

    country_code = address.get("country_code", "").lower()

    if country_code != "us":
        raise ResolveError(
            f"Location must be within the United States: {query!r}"
        )

    # ---------------------------------------------------------
    # Extract coordinates
    # ---------------------------------------------------------
    try:
        lat = float(result["lat"])
        lng = float(result["lon"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ResolveError(
            f"Invalid coordinates returned for location: {query!r}"
        ) from exc

    # ---------------------------------------------------------
    # Final coordinate-range validation
    # ---------------------------------------------------------
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise ResolveError(
            f"Invalid coordinates returned for location: {query!r}"
        )

    return lat, lng