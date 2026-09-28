# Loom Walkthrough Script — Fuel Route API

> **Target duration:** Under 5 minutes  
> **Format:** Spoken walkthrough + live Postman demonstration + concise code tour

**Before recording:** Start the Django server, open Postman with the API collection, and open the `routing/` directory in your editor. Use a route longer than 500 miles so that multiple fuel stops are visible.

---

## 0. Introduction — ~20 seconds

**Say:**

> Hi, I'm Mohamed Fasidh. This is my submission for the Backend Django Engineer coding assessment.
>
> The task is to build an API that takes a start and finish location within the US and returns the driving route, cost-effective fuel stops along that route, and the total fuel cost for a vehicle with a maximum range of 500 miles and fuel economy of 10 miles per gallon.
>
> I'll first show the main design decision, then demonstrate the API in Postman, and finally give a quick code walkthrough.

---

## 1. Architecture and Key Constraint — ~40 seconds

**Say:**

> The supplied fuel-price dataset contains thousands of stations, but the station records do not consistently provide usable latitude and longitude coordinates.
>
> A straightforward approach would be to geocode every station during every API request. That would require thousands of external API calls and would make the API both slow and dependent on external services.
>
> Instead, I preprocess the fuel-price data during import. I deduplicate stations using their OPIS identifiers and resolve city and state against a bundled US-cities dataset to obtain coordinates.
>
> This means the station coordinates are prepared once, offline, before requests arrive.
>
> At request time, the application needs only the routing service to calculate the driving route. Station filtering and fuel optimization are then performed locally in memory.
>
> Let me show the API working.

---

## 2. Live Postman Demonstration — ~90 seconds

### 2.1 Long route

**Do:** Select the `Los Angeles, CA → New York, NY` request and click **Send**.

**Say:**

> Here I'm sending a coast-to-coast request from Los Angeles to New York using place names.

**Do:** Scroll through the JSON response.

**Say:**

> The API returns the route geometry, the total route distance, the fuel cost, and the recommended fuel stops.
>
> In this current run, the route is approximately 2,793 miles.
>
> The current result is approximately 2,793 miles, with a starting fuel cost of about 164 dollars and a total fuel cost of about 863 dollars under the documented full-tank assumption.
>
> The fuel stops are ordered along the route. Each stop contains the station name, location, price per gallon, gallons purchased, purchase cost, and the mile marker along the route.

**Do:** Scroll to `meta`.

**Say:**

> The metadata shows how many stations were considered, how many route points were returned, the corridor width, the vehicle range and MPG, and the server-side processing time.

---

### 2.2 Short route

**Do:** Select the `Oklahoma City, OK → Tulsa, OK` request and click **Send**.

**Say:**

> Here's an important edge case: a short route that can be completed within one tank.

Point to:

```json
{
  "distance_miles": 106.3,
  "starting_fuel_cost_usd": 30.6,
  "total_fuel_cost_usd": 30.6,
  "fuel_stops": []
}
```

**Say:**

> The distance is about 106 miles, so no additional refueling stop is required.
>
> Notice that `fuel_stops` is empty, but the total fuel cost is not zero. The vehicle still consumes fuel, and my documented starting-fuel assumption accounts for the initial full tank.

---

### 2.3 Impossible route

**Do:** Select the `Honolulu, HI → Los Angeles, CA` request and click **Send**.

**Say:**

> Finally, here's an invalid driving scenario. Honolulu to Los Angeles has no drivable road connection.
>
> The API handles that cleanly with a 422 response and an error message instead of returning invalid route data or crashing.

---

### 2.4 Optional map

**Do:** Open `/map/` in the browser if available.

**Say:**

> I also included a simple Leaflet visualization that displays the route and the selected fuel stops on a map.

> **If time is tight, skip this section.**

---

## 3. Code Walkthrough — ~100 seconds

### Point 1 — Data preprocessing and routing

**Do:** Open:

```text
routing/management/commands/import_fuel_prices.py
```

**Say:**

> The import command preprocesses the supplied fuel-price CSV.
>
> Stations are deduplicated using their OPIS identifiers, and city and state information is matched against the bundled US-cities dataset to obtain coordinates.
>
> This preprocessing avoids expensive station-by-station geocoding during API requests.

**Do:** Open:

```text
routing/views.py
```

**Say:**

> On the request path, the application resolves the start and finish locations, requests the driving route from OSRM, and then performs the station filtering and fuel optimization locally.
>
> The goal is to keep external routing calls to a minimum.

---

### Point 2 — Route corridor matching

**Do:** Open:

```text
routing/services/geo.py
```

**Say:**

> Once the route polyline is available, I identify fuel stations within a configurable corridor around the route.
>
> A KD-tree is used to efficiently narrow the station set to nearby candidates. The candidates are then checked against the route geometry and projected to a mile marker along the route.
>
> This keeps the expensive spatial work local rather than making an external request for every station.

---

### Point 3 — Fuel optimization

**Do:** Open:

```text
routing/services/fuel.py
```

**Say:**

> The total amount of fuel consumed is determined by route distance divided by the vehicle's 10 MPG efficiency.
>
> The optimization problem is therefore where to purchase that fuel while respecting the vehicle's 500-mile maximum range.
>
> The optimizer evaluates reachable stations and favors lower-priced fuel while ensuring that every leg of the journey remains within the vehicle's range.

**Do:** Briefly show:

```text
routing/tests/test_fuel.py
```

**Say:**

> The fuel logic is covered by tests, including randomized cases comparing the greedy strategy against a brute-force reference implementation.

> **Only say “provably optimal” if the repository contains a formal proof or your test suite explicitly establishes the exact mathematical conditions required for that claim.**

---

## 4. Testing — ~20 seconds

**Do:** Show the terminal:

```bash
python manage.py test
```

**Say:**

> The Django test suite currently passes all 16 tests.

Show:

```text
Ran 16 tests
OK
```

**Optional:** Also show:

```bash
python manage.py check
```

with:

```text
System check identified no issues (0 silenced).
```

---

## 5. Closing — ~20 seconds

**Say:**

> So, to summarize: the API accepts US locations, calculates a driving route, identifies fuel stations along the route, selects cost-effective refueling points while respecting the 500-mile vehicle range, and returns the total fuel cost.
>
> The station data is preprocessed offline, external routing calls are minimized, and the remaining station matching and optimization work is performed locally.
>
> The project includes the Django implementation, tests, setup instructions, Postman examples, and documentation in the repository.
>
> Thanks for watching.

---

## Quick Recording Checklist

Before starting the Loom:

- [ ] Django server is running.
- [ ] Fuel-price CSV has been imported.
- [ ] Postman collection is open.
- [ ] Long-route request is ready.
- [ ] Short-route request is ready.
- [ ] No-route request is ready.
- [ ] Editor is open to `routing/`.
- [ ] `python manage.py test` passes.
- [ ] README is updated.
- [ ] Postman testing guide is updated.
- [ ] Do not quote outdated `$699` fuel-cost figures.
- [ ] Use the current API output when describing actual results.
- [ ] Keep the final recording below 5 minutes.

---

## Recommended Timing

| Section | Target |
|---|---:|
| Introduction | 20 sec |
| Architecture / constraint | 40 sec |
| Postman demo | 90 sec |
| Code walkthrough | 100 sec |
| Tests | 20 sec |
| Closing | 20 sec |
| **Total** | **~4 min 50 sec** |

> **Tip:** Keep the code walkthrough focused. The reviewer does not need every file explained. Demonstrating the architecture, routing call, spatial filtering, optimization logic, and passing tests is enough for a concise assessment walkthrough.

---

> **Important accuracy note:** The normal route path is designed to minimize external calls. If a request requires fallback geocoding, an additional geocoding request may occur. In the Loom, describe the normal cached/local-data path rather than claiming that every possible request always makes exactly one external call.
