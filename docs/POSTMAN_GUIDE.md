# Postman Testing Guide — Fuel Route API

## Prerequisites

Start Django:

```bash
python manage.py runserver
```

Base URL:

```text
http://127.0.0.1:8000
```

Make sure the fuel-price dataset has been imported:

```bash
python manage.py import_fuel_prices
```

---

## 1. Long route — Los Angeles to New York

### Request

```http
GET http://127.0.0.1:8000/route/?start=Los%20Angeles,%20CA&finish=New%20York,%20NY
```

### What to verify

The response should contain:

```json
{
  "route": {
    "type": "LineString",
    "coordinates": []
  },
  "distance_miles": 0,
  "total_fuel_cost_usd": 0,
  "fuel_stops": [],
  "meta": {}
}
```

The actual numeric values depend on the current OSRM route and imported fuel-price dataset.

### Important fuel-cost interpretation

The vehicle starts with a full 500-mile tank.

Therefore:

- The initial 50 gallons are assumed to already be available.
- The API does **not** charge the initial tank in `total_fuel_cost_usd`.
- `total_fuel_cost_usd` is the cost of additional fuel purchased at the returned fuel stops.
- `fuel_stops` are ordered along the route.

Each stop contains:

```text
name
city
state
lat
lng
price_per_gallon
gallons
cost_usd
mile_marker
```

---

## 2. Short route — Oklahoma City to Tulsa

### Request

```http
GET http://127.0.0.1:8000/route/?start=Oklahoma%20City,%20OK&finish=Tulsa,%20OK
```

A route that is shorter than the vehicle's 500-mile initial range may require no additional purchase.

For such a case, the correct response pattern is:

```json
{
  "fuel_stops": [],
  "total_fuel_cost_usd": 0.0
}
```

This is not an error. The initial tank is assumed to be full before the trip begins.

---

## 3. Impossible route — Honolulu to Los Angeles

### Request

```http
GET http://127.0.0.1:8000/route/?start=Honolulu,%20HI&finish=Los%20Angeles,%20CA
```

Expected behavior:

```http
422
```

The API should return an error because there is no drivable road route between the two locations.

---

## 4. Coordinate input

The endpoint also accepts latitude/longitude:

```http
GET http://127.0.0.1:8000/route/?start=34.05,-118.24&finish=40.71,-74.01
```

---

## 5. Full route geometry

By default, the response geometry is simplified for a smaller response payload.

To return the full OSRM geometry:

```http
GET http://127.0.0.1:8000/route/?start=Los%20Angeles,%20CA&finish=New%20York,%20NY&geometry=full
```

---

## 6. API specification

Open:

```http
GET http://127.0.0.1:8000/api/
```

This returns the machine-readable API specification.

---

## 7. Map demo

Open:

```text
http://127.0.0.1:8000/map/
```

The Leaflet demo displays the route and selected fuel stops.

---

## 8. What to show during the assessment

For the Loom demonstration:

1. Send the long Los Angeles → New York request.
2. Show `distance_miles`, `total_fuel_cost_usd`, and `fuel_stops`.
3. Show a short route where no additional fuel purchase is required.
4. Show the Honolulu → Los Angeles 422 response.
5. Briefly show `views.py`, `geo.py`, `fuel.py`, and the tests.
6. Run:

```bash
python manage.py check
python manage.py test
```

Do not quote hard-coded fuel-cost values from an earlier run. Use the values returned by the current API run.
