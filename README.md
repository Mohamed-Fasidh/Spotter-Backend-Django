# Fuel Route API

Backend Django coding assessment: calculate a driving route between two US locations, identify cost-effective fuel stops along the route, and return the additional fuel cost required to complete the journey.

## Fuel-cost model

The vehicle starts the trip with a full tank.

- Maximum vehicle range: **500 miles**
- Fuel economy: **10 MPG**
- Full tank equivalent: **50 gallons**
- The initial full tank is assumed to already be available at the origin.
- `total_fuel_cost_usd` represents **only additional fuel purchased during the journey**.
- The API does **not** assign a monetary cost to the initial fuel already in the tank.

Therefore, a route that can be completed entirely with the initial tank can correctly return:

```json
{
  "fuel_stops": [],
  "total_fuel_cost_usd": 0.0
}
```

## API

### `GET /route/`

Required query parameters:

- `start`: `lat,lng` or a US place name such as `Dallas, TX`
- `finish`: `lat,lng` or a US place name

Optional:

- `geometry=simplified` (default)
- `geometry=full`

Example:

```text
GET /route/?start=Los Angeles, CA&finish=New York, NY
```

The response contains:

- `route`: GeoJSON `LineString`
- `distance_miles`
- `total_fuel_cost_usd`
- `fuel_stops`
- `meta`

Each fuel stop includes station information, price per gallon, gallons purchased, purchase cost, and route mile marker.

## Routing and performance

The application uses OSRM for driving-route calculation.

The request path is designed to minimize external calls:

1. Start and finish are resolved locally from the bundled US cities data when possible.
2. One OSRM routing request calculates the driving route.
3. Fuel stations are filtered locally using the route geometry and a KD-tree.
4. Fuel optimization is performed locally in memory.

Fuel-price station coordinates are prepared during the fuel-data import process rather than geocoding every station during each API request.

## Fuel optimization

The optimizer starts with the vehicle's full 500-mile range and only records fuel purchased at stations.

At each reachable station, it considers whether a cheaper station can be reached within the remaining vehicle range. It purchases enough fuel to reach that cheaper station when appropriate; otherwise it purchases enough to cover the required distance while respecting the 500-mile range.

The fuel tests include comparisons against a brute-force reference implementation for randomized cases.

## HTTP responses

- `200`: route found
- `400`: invalid or unresolved start/finish
- `422`: no drivable route or route cannot be completed within the vehicle range
- `502`: routing service unavailable

## Running locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python manage.py check
python manage.py test
```

Import the supplied fuel-price data before using the route endpoint:

```bash
python manage.py import_fuel_prices
```

Run the development server:

```bash
python manage.py runserver
```

## Demo endpoints

- `/route/` — route and fuel-planning API
- `/map/` — Leaflet map demo
- `/api/` — machine-readable API specification
- `/` — human-readable API documentation

## Project structure

```text
config/
routing/
  management/commands/import_fuel_prices.py
  services/
    fuel.py
    geo.py
    osrm.py
    resolve.py
  tests/
  templates/
docs/
  LOOM_SCRIPT.md
  POSTMAN_GUIDE.md
data/
fuel-prices-for-be-assessment.csv
requirements.txt
manage.py
```
