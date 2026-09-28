# Fuel Route API

> **Spotter Backend Django Engineer — Coding Assessment**

A Django-based API that accepts a start and finish location in the USA
and returns a driving route, cost-effective fuel stops, total fuel
cost, and vehicle/processing metadata.

The implementation focuses on **correctness**, **low external API
usage**, **fast in-memory processing**, and a **simple clone-and-run
setup**.

**Endpoint**

`GET /route/?start=<place|lat,lng>&finish=<place|lat,lng>`

**Stack**

`Django 6.1.1` · `Python 3.12+` · `SQLite` · `NumPy` · `SciPy` ·
`Requests` · `python-dotenv`

---

GET /route/?start=<place|lat,lng>&finish=<place|lat,lng>

Built with Django 6.1.1, Python 3.12+, SQLite, NumPy, SciPy,
Requests, and python-dotenv.

## Table of Contents

- [Assignment Requirements Covered](#assignment-requirements-covered)
- [The Core Design Decision](#the-core-design-decision)
- [Setup](#setup)
- [API Usage](#api-usage)
- [Endpoints](#endpoints)
- [Vehicle and Fuel Assumptions](#vehicle-and-fuel-assumptions)
- [Fuel Optimization](#fuel-optimization)
- [Route Corridor Matching](#route-corridor-matching)
- [Geocoding Strategy](#geocoding-strategy)
- [External Services](#external-services)
- [Performance Design](#performance-design)
- [Response Example](#response-example)
- [Response Fields](#response-fields)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Postman](#postman)
- [Loom Demo](#loom-demo)
- [Data Notes](#data-notes)
- [Configuration](#configuration)
- [Error Handling](#error-handling)
- [Why Plain Django Instead of Django REST Framework?](#why-plain-django-instead-of-django-rest-framework)
- [Production Considerations](#production-considerations)
- [Design Summary](#design-summary)

---

## Assignment Requirements Covered

| Requirement | Implementation |
|---|---|
| **Start and finish locations in the USA** | Place names or `lat,lng` coordinates |
| **Return a route** | OSRM driving route returned as GeoJSON |
| **Recommend fuel stops** | Stations within a configurable route corridor |
| **Cost-effective fuel selection** | Greedy gas-station optimization |
| **Vehicle maximum range** | `500 miles` |
| **Fuel economy** | `10 MPG` |
| **Multiple fuel stops** | Supported for long routes |
| **Total fuel cost** | Initial full-tank cost plus fuel purchased at selected stations |
| **Fuel-price source** | Supplied assessment CSV |
| **Free routing API** | Public OSRM routing service |
| **Minimize external calls** | Offline city lookup first; one OSRM routing call per uncached route |
| **Django** | Django `6.1.1` |
| **API response speed** | In-memory station cache, KD-tree filtering, compact response geometry |
| **API demonstration** | Postman guide and smoke-test script |
| **Code overview** | 5-minute-or-less Loom script |
| **GitHub submission** | Repository-ready project structure |

## The Core Design Decision


The supplied fuel-price CSV contains station information such as
city/state and highway-exit-style addresses, but it does not provide
usable latitude/longitude coordinates for every station.

A naive implementation would geocode thousands of stations during every
API request. That would be slow, expensive in external requests, and
would violate the spirit of the assessment's routing-call constraint.

Instead, the project performs the expensive station-location work once
during the import process:

Fuel-price CSV
      |
      v
Deduplicate by OPIS Truckstop ID
      |
      v
Join City + State against bundled US city coordinates
      |
      v
Store station coordinates in SQLite

At request time:

Start + Finish
      |
      v
Offline city lookup
      |
      +---- miss ----> Nominatim fallback
      |
      v
One OSRM routing request
      |
      v
Route geometry + distance
      |
      v
KD-tree corridor filtering
      |
      v
Point-to-segment projection
      |
      v
Ordered fuel stations
      |
      v
Greedy fuel optimization
      |
      v
JSON response + optional Leaflet map

The station matching and fuel optimization are performed locally in
memory. No per-station external API requests are made.

## Setup


1. Create a virtual environment

### Windows PowerShell

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```bash
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Configure environment variables

Copy .env.example to .env.

Example:

```bash
DJANGO_SECRET_KEY=replace-with-a-local-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
GEOCODER_USER_AGENT=spotter-fuelroute-assessment/1.0
```

Do not commit .env to GitHub.

4. Apply migrations

```bash
python manage.py migrate
```

5. Import the supplied fuel-price data

```bash
python manage.py import_fuel_prices fuel-prices-for-be-assessment.csv
```

The import command:

Reads the supplied CSV.

Deduplicates stations by OPIS Truckstop ID.

Uses the lowest available price for duplicate OPIS IDs.

Resolves station city/state against the bundled US city dataset.

Stores usable stations in SQLite.

No geocoding API calls are required during the import.

6. Start Django

```bash
python manage.py runserver
```

The API is then available at:

```bash
http://127.0.0.1:8000/
```

## API Usage


### Coast-to-coast example

```bash
curl "http://127.0.0.1:8000/route/?start=Los%20Angeles,%20CA&finish=New%20York,%20NY"
```

### Coordinate example

```bash
curl "http://127.0.0.1:8000/route/?start=34.05,-118.24&finish=40.71,-74.01"
```

### Full route geometry

By default, the response geometry is simplified for a smaller payload.

To return the complete OSRM route geometry:

```bash
curl "http://127.0.0.1:8000/route/?start=Los%20Angeles,%20CA&finish=New%20York,%20NY&geometry=full"
```

## Endpoints


GET /route/

Main route-planning endpoint.

### Query parameters

Parameter               Required                Description

start                 Yes                     lat,lng or a place
name such as
Dallas, TX

finish                Yes                     lat,lng or a place
name

### Success

HTTP 200

### Errors

400 - Missing or unresolvable start/finish
422 - No drivable route or route cannot be completed within 500-mile range
502 - Routing service unavailable

GET /

Human-readable API documentation.

GET /api/

Machine-readable API specification.

GET /map/

Interactive Leaflet demonstration page showing the route and selected
fuel stops.

## Vehicle and Fuel Assumptions


The assessment specifies:

Maximum vehicle range = 500 miles
Fuel economy            = 10 MPG

Therefore:

Tank capacity = 500 / 10 = 50 gallons

### Starting fuel assumption

The assignment does not specify the amount of fuel in the vehicle when
the trip starts.

This implementation assumes the vehicle starts with a full 50-gallon
tank, based on the 500-mile maximum range and 10 MPG fuel economy.

The total_fuel_cost_usd includes the cost of the initial full tank
plus any additional fuel purchased at selected stations along the route.

The initial full-tank cost is calculated using the price at the first
selected fueling location. This makes the total fuel cost explicit and
prevents the initial fuel from being treated as free.

This assumption is explicitly kept in the API documentation.

### Range constraint

Every driving leg must be no more than 500 miles:

```bash
origin -> first fuel stop
first stop -> second stop
...
last fuel stop -> destination
```

If no valid fuel plan exists within the 500-mile range, the API returns:

HTTP 422

rather than silently returning an invalid route.

## Fuel Optimization


The implementation uses the classic gas-station greedy strategy.

Stations are ordered by their distance from the beginning of the route.

At the current station:

Search for a cheaper reachable station within the vehicle's
remaining range.

If a cheaper station exists, purchase only enough fuel to reach it.

If no cheaper station is reachable, purchase enough fuel to cover
the next required distance, up to the tank capacity.

Continue until the destination is reachable.

Conceptually:

Current station
      |
      +-- cheaper station reachable?
      |          |
      |          +-- YES --> buy only enough to reach it
      |
      +-- NO --> fill as needed, subject to the remaining trip distance

This minimizes fuel purchase cost under the model's assumptions of:

Fixed fuel consumption.

Fixed tank range.

Known station prices.

No fuel consumed while stopped.

No additional station-specific constraints.

The implementation is also tested against a brute-force/fine-grid
optimization approach over randomized cases in
routing/tests/test_fuel.py.

## Route Corridor Matching


A fuel station is considered relevant when its stored city-centroid
coordinate is within:

5 miles

of the routed polyline.

The setting is:

`CORRIDOR_MILES = 5.0`

The matching process is:

OSRM route polyline
      |
      v
Route vertices in local planar coordinates
      |
      v
KD-tree prefilter
      |
      v
Exact point-to-segment distance
      |
      v
Stations within 5 miles
      |
      v
Projection onto route
      |
      v
Mile marker

The KD-tree significantly reduces the number of stations that require
the more expensive point-to-segment calculation.

## Geocoding Strategy


Place names

For a place-name input such as:

Los Angeles, CA

the resolver checks the bundled city dataset first.

This avoids an external geocoding request for common locations.

If a location is not found in the bundled dataset, the implementation
can fall back to the public Nominatim service with a US country
restriction.

Coordinates

Coordinates can also be supplied directly:

```bash
34.05,-118.24
```

The resolver validates latitude and longitude ranges before using them.

For assessment inputs, coordinates should represent locations within the
USA.

### External call behavior

A typical request using cities already present in the bundled dataset
requires:

0 geocoding calls
+
1 OSRM routing call

If one or both endpoints are not present in the offline city table,
Nominatim may be used as a fallback:

up to 2 endpoint geocoding calls
+
1 OSRM routing call

External responses are cached where applicable.

## External Services


OSRM

The application uses the public OSRM routing service:

```bash
https://router.project-osrm.org/route/v1/driving
```

OSRM provides:

Driving route geometry.

Route distance.

The application makes one routing request per uncached route.

### Nominatim

The fallback geocoder is:

```bash
https://nominatim.openstreetmap.org/search
```

It is only used when the bundled city lookup does not resolve an
endpoint.

The application identifies itself using the configured:

GEOCODER_USER_AGENT

### Public-service limitation

The public OSRM and Nominatim services are shared public infrastructure
and should not be treated as production-scale infrastructure.

For production, OSRM could be self-hosted and the base URL changed
through configuration.

## Performance Design


The main performance goal is to avoid repeated external calls and
expensive per-request database work.

1. Offline station coordinates

Station coordinates are resolved during the import process rather than
during every API request.

2. In-memory station cache

The station table is loaded into NumPy arrays and reused across
requests.

This avoids querying the database once per station on every route
request.

3. KD-tree filtering

A scipy.spatial.cKDTree is built over route vertices to narrow the
station candidate set before the exact point-to-segment calculation.

4. Downsampled route matching

OSRM can return a large number of route vertices. Corridor matching uses
at most 2,000 representative vertices to bound the in-memory geometry
operation.

The route's reported distance from OSRM remains the authoritative trip
distance.

5. Compact response geometry

The default response returns a simplified route geometry of at most
approximately 600 points.

Use:

```bash
?geometry=full
```

when the complete route geometry is required.

This affects the response payload only; the fuel calculation is
performed before the display geometry is reduced.

6. Cached routing and geocoding

Repeated identical routing and fallback geocoding operations can reuse
cached results, reducing unnecessary external network requests.

## Response Example


A successful response has this general structure:

{
  "route": {
    "type": "LineString",
    "coordinates": [
      [-118.2437, 34.0522],
      [-118.1000, 34.2000]
    ]
  },
  "distance_miles": 2793.4,
  "starting_fuel_cost_usd": 164.12,
  "total_fuel_cost_usd": 1027.33,
  "fuel_stops": [
    {
      "name": "Example Fuel Station",
      "city": "North Las Vegas",
      "state": "NV",
      "lat": 36.19881,
      "lng": -115.12281,
      "price_per_gallon": 3.282,
      "gallons": 26.09,
      "cost_usd": 85.64,
      "mile_marker": 260.9
    }
  ],
  "meta": {
    "stations_considered": 365,
    "route_points": 600,
    "geometry": "simplified",
    "corridor_miles": 5.0,
    "vehicle_range_miles": 500.0,
    "vehicle_mpg": 10.0,
    "elapsed_ms": 374.0
  }
}
```

The exact distance, stations, prices, and elapsed time depend on the
current routing response and imported fuel-price dataset.

## Response Fields


**`route`**

GeoJSON LineString containing the driving route.

**`distance_miles`**

Total driving distance reported by OSRM, converted from meters to miles.

**`starting_fuel_cost_usd`**

Cost of the initial full 50-gallon tank using the first selected
fueling location price.

**`total_fuel_cost_usd`**

Total fuel cost for the trip, including the initial full tank and
all subsequent fuel purchased at selected stations.

**`fuel_stops`**

Ordered list of selected fuel stations.

Each stop includes:

Station name.

City.

State.

Latitude/longitude.

Price per gallon.

Gallons purchased.

Cost of the purchase.

Mile marker along the route.

**`meta`**

Contains:

Number of candidate stations considered.

Number of route points returned.

Geometry mode.

Corridor width.

Vehicle range.

Vehicle MPG.

Request elapsed time.

## Project Structure


```text
Spotter-Backend-Django-Main/
│
├── manage.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── test_api.sh
├── fuel-prices-for-be-assessment.csv
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── routing/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   │
│   ├── management/
│   │   └── commands/
│   │       └── import_fuel_prices.py
│   │
│   ├── services/
│   │   ├── cities.py
│   │   ├── resolve.py
│   │   ├── osrm.py
│   │   ├── geo.py
│   │   └── fuel.py
│   │
│   ├── migrations/
│   │   └── 0001_initial.py
│   │
│   ├── templates/
│   │   └── routing/
│   │       ├── map.html
│   │       └── docs.html
│   │
│   └── tests/
│       ├── test_fuel.py
│       ├── test_geo.py
│       ├── test_resolve.py
│       └── test_view.py
│
├── data/
│   └── uscities.csv
│
└── docs/
    ├── POSTMAN_GUIDE.md
    └── LOOM_SCRIPT.md
```

## Testing


Run the Django test suite:

```bash
python manage.py test
```

The tests cover:

Fuel optimization.

Greedy solution versus brute-force/fine-grid validation.

Infeasible routes.

Geometry corridor matching.

Station ordering and mile markers.

Coordinate parsing.

Offline endpoint resolution.

API success responses.

API validation errors.

Routing error handling.

API smoke test

Start Django:

```bash
python manage.py runserver
```

Then, in another terminal:

```bash
./test_api.sh
```

Or specify another base URL:

```bash
./test_api.sh http://host:port
```

The smoke test exercises successful and error scenarios and returns a
non-zero exit status when an assertion fails.

## Postman


A complete Postman walkthrough is available here:

docs/POSTMAN_GUIDE.md

It covers:

Coast-to-coast route.

Coordinate input.

Short route.

Infeasible route.

Invalid/missing input.

API specification.

HTML documentation.

Automated assertions.

## Loom Demo


The Loom script is available here:

docs/LOOM_SCRIPT.md

The intended demonstration is under five minutes and covers:

Project purpose.

Architecture.

Postman request.

API response.

Fuel-stop optimization.

Code structure.

Testing and performance design.

## Data Notes


The supplied assessment CSV contains fuel-price records identified by
OPIS Truckstop ID.

The import process:

8,151 source rows
        |
        v
deduplicate by OPIS Truckstop ID
        |
        v
6,738 unique station records
        |
        v
city/state coordinate lookup
        |
        v
stations with usable US coordinates

The bundled city dataset is used only as an offline coordinate source
for the station import and endpoint lookup.

Some source records may not resolve to a US city coordinate and are
therefore not available for route-corridor matching.

## Configuration


The main fuel-routing settings are in:

config/settings.py

Vehicle

`VEHICLE_RANGE_MILES = 500.0`
`VEHICLE_MPG = 10.0`

Route corridor

`CORRIDOR_MILES = 5.0`

OSRM

`OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving"`

Nominatim

`NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"`

HTTP timeout

`EXTERNAL_HTTP_TIMEOUT = 15`

These values are configurable without changing the core routing and
optimization algorithms.

## Error Handling


The API intentionally separates client errors from external-service
errors.

### 400 Bad Request

Returned when:

start is missing.

finish is missing.

An endpoint cannot be resolved.

An endpoint contains invalid coordinate input.

Example:

{
  "error": "start and finish are required."
}

### 422 Unprocessable Entity

Returned when:

OSRM cannot find a drivable route.

The route exists but cannot be completed within the 500-mile vehicle
range.

### 502 Bad Gateway

Returned when the external routing service cannot be reached.

This distinction makes the API behavior clearer for clients and easier
to debug.

## Why Plain Django Instead of Django REST Framework?


The assignment requires a small read-only API with one primary endpoint.

The implementation therefore uses Django's built-in JsonResponse and
ordinary Django views rather than adding Django REST Framework.

This keeps the dependency set small and makes the project easy to clone,
install, migrate, import, and run.

## Production Considerations


This project is intentionally optimized for the coding-assessment
requirements, not presented as a complete production deployment.

For production:

### Routing

Self-host OSRM or use a production routing provider rather than relying
on the public OSRM demo server.

### Database

SQLite is sufficient for the assessment's read-mostly single-table
workload. For a larger deployment, PostgreSQL would be a natural choice.

### Spatial database

If PostgreSQL/PostGIS is introduced, station corridor filtering could be
moved from the in-memory NumPy implementation to spatial database
queries such as ST_DWithin.

### Caching

A shared cache such as Redis could replace process-local caches when
running multiple application workers.

### Security

Production deployment should use:

DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<secure-random-secret>
DJANGO_ALLOWED_HOSTS=<production-hosts>

and HTTPS, appropriate proxy/security settings, and proper process
management.

## Design Summary


The implementation intentionally keeps the request path small:

             ```text
+------------------+
             |  Start / Finish  |
             +--------+---------+
                      |
                      v
             +------------------+
             | Endpoint Resolver|
             | Offline -> Nomin.|
             +--------+---------+
                      |
                      v
             +------------------+
             |      OSRM        |
             | 1 route request  |
             +--------+---------+
                      |
                      v
             +------------------+
             | Route Geometry   |
             +--------+---------+
                      |
                      v
             +------------------+
             | KD-tree + Geo    |
             | Corridor Match   |
             +--------+---------+
                      |
                      v
             +------------------+
             | Fuel Optimizer   |
             | Greedy Strategy  |
             +--------+---------+
                      |
                      v
             +------------------+
             | JSON Response    |
             | + Leaflet Map    |
             +------------------+
```

The main engineering choices are:

Offline station coordinate preparation.

Minimal external routing calls.

Cached endpoint and route resolution.

In-memory NumPy/SciPy processing.

Explicit 500-mile feasibility checks.

Cost-aware greedy fuel purchasing.

Small default response payload.

Automated unit tests.

Plain Django with minimal dependencies.
