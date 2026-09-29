# Loom Walkthrough Script — Fuel Route API

> **Target duration:** Under 5 minutes  
> **Format:** Spoken walkthrough + live Postman demonstration + concise code tour

---

## Before Recording

Before starting the Loom:

- Start the Django server.
- Open Postman with the API collection.
- Open the `routing/` directory in your editor.
- Have one route longer than 500 miles ready so that fuel stops are visible.
- Have one short route ready that can be completed within the initial full tank.
- Have the impossible/no-route example ready.
- Run the test suite before recording.

---

# 0. Introduction — ~20 seconds

### Say:

> Hi, I'm Mohamed Fasidh. This is my submission for the Backend Django Engineer coding assessment.
>
> The task is to build an API that takes a start and finish location within the US and returns the driving route, cost-effective fuel stops along that route, and the total fuel cost for a vehicle with a maximum range of 500 miles and fuel economy of 10 miles per gallon.
>
> I'll first explain the main design decision, then demonstrate the API in Postman, and finally give a quick code walkthrough.

---

# 1. Architecture and Key Constraint — ~40 seconds

### Say:

> The supplied fuel-price dataset contains thousands of stations, but the station records do not consistently provide usable latitude and longitude coordinates.
>
> A straightforward approach would be to geocode every station during every API request. That would require thousands of external API calls and would make the API both slow and dependent on external services.
>
> Instead, I preprocess the fuel-price data during import. I deduplicate stations using their OPIS identifiers and resolve city and state information against a bundled US-cities dataset to obtain coordinates.
>
> This means the station coordinates are prepared once during preprocessing rather than geocoding every station on every request.
>
> At request time, the application obtains the driving route from OSRM. Station filtering and fuel optimization are then performed locally in memory.
>
> Let me show the API working.

---

# 2. Live Postman Demonstration — ~90 seconds

## 2.1 Long Route

### Do:

Select the:

`Los Angeles, CA → New York, NY`

request and click **Send**.

### Say:

> Here I'm sending a coast-to-coast request from Los Angeles to New York using place names.

### Do:

Scroll through the JSON response.

### Say:

> The API returns the route geometry, the total route distance, the total cost of additional fuel purchased, and the recommended fuel stops.
>
> The fuel stops are ordered along the route. Each stop contains the station name, location, price per gallon, gallons purchased, purchase cost, and mile marker.

If you mention the distance, read the current value from Postman. Do not use a memorized fuel-cost figure.

### Then scroll to `meta`.

### Say:

> The metadata shows how many stations were considered, how many route points were returned, the corridor width, the vehicle range and MPG, and the server-side processing time.

---

## 2.2 Short Route

### Do:

Select:

`Oklahoma City, OK → Tulsa, OK`

and click **Send**.

### Say:

> Here's an important edge case: a short route that can be completed using the fuel already in the vehicle's initial full tank.

### Point to:

```json
{
  "distance_miles": 106.3,
  "total_fuel_cost_usd": 0.0,
  "fuel_stops": []
}
```

Only use `106.3` if that is the current Postman result.

### Say:

> The distance is within the vehicle's 500-mile starting range.
>
> Therefore, no additional fuel purchase is required and `fuel_stops` is empty.
>
> The vehicle consumes fuel during the trip, but because it starts with a full tank and the trip fits within that available range, no additional fuel needs to be purchased. Therefore the reported fuel purchase cost is zero.

---

## 2.3 Impossible Route

### Do:

Select:

`Honolulu, HI → Los Angeles, CA`

and click **Send**.

### Say:

> Finally, here's an invalid driving scenario. Honolulu to Los Angeles has no drivable road connection.
>
> The API handles that cleanly with a 422 response and an error message instead of returning invalid route data or crashing.

---

## 2.4 Optional Map — ~10 seconds

### Do:

Open:

`/map/`

in the browser if available.

### Say:

> I also included a simple Leaflet visualization that displays the route and the selected fuel stops on a map.

If time is tight, skip this section.

---

# 3. Code Walkthrough — ~100 seconds

## Point 1 — Data Preprocessing and Routing

### Do:

Open:

`routing/management/commands/import_fuel_prices.py`

### Say:

> The import command preprocesses the supplied fuel-price CSV.
>
> Stations are deduplicated using their OPIS identifiers, and city and state information is matched against the bundled US-cities dataset to obtain coordinates.
>
> This preprocessing avoids expensive station-by-station geocoding during API requests.

### Do:

Open:

`routing/views.py`

### Say:

> On the request path, the application resolves the start and finish locations, requests the driving route from OSRM, and then performs station filtering and fuel optimization locally.
>
> The API is designed to minimize external routing and geocoding calls while keeping the request-time computation lightweight.

---

## Point 2 — Route Corridor Matching

### Do:

Open:

`routing/services/geo.py`

### Say:

> Once the route polyline is available, I identify fuel stations within a configurable corridor around the route.
>
> A KD-tree is used to efficiently narrow the station set to nearby candidates.
>
> The candidates are then checked against the route geometry and projected to a mile marker along the route.
>
> This keeps the spatial processing local instead of making an external request for every fuel station.

---

## Point 3 — Fuel Optimization

### Do:

Open:

`routing/services/fuel.py`

### Say:

> The vehicle has a maximum range of 500 miles and achieves 10 miles per gallon.
>
> The optimizer starts with a full tank, which corresponds to 50 gallons.
>
> Therefore, the optimizer only calculates additional fuel that needs to be purchased during the journey.
>
> At each station, it checks whether a cheaper reachable station exists within the vehicle's range. If one exists, it purchases enough fuel to reach that station. Otherwise, it purchases enough to continue the journey while respecting the tank range.
>
> The result is an ordered list of fuel purchases and the total cost of those purchases.

### Do:

Briefly show:

`routing/tests/test_fuel.py`

### Say:

> The fuel logic is covered by tests, including comparisons against a brute-force reference implementation for the tested cases.

Only say "provably optimal" if the repository contains the appropriate formal proof or the tests establish the exact mathematical conditions needed for that claim.

---

# 4. Testing — ~20 seconds

### Do:

Show the terminal:

```bash
python manage.py test
```

### Say:

> The Django test suite validates the API, fuel optimization, route handling, error cases, and geometry behavior.

Use the actual test count displayed by the terminal. Do not hard-code a test count unless the current terminal actually reports it.

### Optional:

Run:

```bash
python manage.py check
```

and show:

```text
System check identified no issues (0 silenced).
```

### Say:

> Django's system checks also report no issues.

---

# 5. Closing — ~20 seconds

### Say:

> So, to summarize: the API accepts US locations, calculates a driving route, identifies fuel stations along the route, selects cost-effective refueling points while respecting the 500-mile vehicle range, and returns the cost of additional fuel purchased during the journey.
>
> The vehicle starts with a full tank, so fuel already present at the origin is not charged again.
>
> The station data is preprocessed offline, external routing calls are minimized, and the remaining station matching and optimization work is performed locally.
>
> The project includes the Django implementation, tests, setup instructions, Postman examples, and documentation in the repository.
>
> Thanks for watching.

---

# Quick Recording Checklist

Before starting the Loom:

- [ ] Django server is running.
- [ ] Fuel-price CSV has been imported.
- [ ] Postman collection is open.
- [ ] Long-route request is ready.
- [ ] Short-route request is ready.
- [ ] No-route request is ready.
- [ ] Editor is open to `routing/`.
- [ ] `python manage.py test` passes.
- [ ] `python manage.py check` passes.
- [ ] README is updated.
- [ ] Postman testing guide is updated.
- [ ] Loom script matches the current API response.
- [ ] No outdated `starting_fuel_cost_usd` references remain.
- [ ] No outdated `$699`, `$863`, or other hard-coded fuel-cost figures are quoted unless they match the current live response.
- [ ] Use the actual current Postman output when describing numerical results.
- [ ] Keep the final recording below 5 minutes.

---

# Recommended Timing

| Section | Target |
|---|---:|
| Introduction | 20 sec |
| Architecture / constraint | 40 sec |
| Postman demo | 90 sec |
| Code walkthrough | 100 sec |
| Tests | 20 sec |
| Closing | 20 sec |
| **Total** | **~4 min 50 sec** |

---

> **Tip:** Keep the code walkthrough focused. The reviewer does not need every file explained. Demonstrating the architecture, routing call, spatial filtering, optimization logic, and passing tests is enough for a concise assessment walkthrough.

---

# Important Accuracy Notes

## Fuel-cost definition

The current implementation uses this model:

```text
Initial tank:
500 miles range
÷ 10 MPG
= 50 gallons
```

The vehicle leaves the origin with that full tank.

Therefore:

```text
total_fuel_cost_usd
=
cost of additional fuel purchased during the journey
```

It does not include the monetary value of fuel already present in the initial tank.

## External API calls

Do not claim that every request always makes exactly one external API call.

A safer explanation is:

> The normal request path minimizes external calls. Route calculation uses the routing service, while station filtering and fuel optimization are performed locally. If endpoint resolution requires fallback geocoding, an additional external request may occur.

## Numerical results

Never memorize the fuel cost from an earlier run.

For the Loom, read the current value directly from Postman. This avoids a mismatch between the recording and the submitted code/data.

## Test count

Never state a fixed number of tests unless the current command actually reports it.

Use:

```bash
python manage.py test
```

immediately before recording.
