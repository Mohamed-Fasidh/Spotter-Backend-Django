# Loom Walkthrough Script — Fuel Route API

**Target duration:** Under 5 minutes  
**Format:** Spoken walkthrough + live Postman demonstration + concise code tour

## 0. Introduction — ~20 seconds

**Say:**

> Hi, I'm Mohamed Fasidh. This is my submission for the Backend Django Engineer coding assessment.
>
> The task is to build an API that takes a start and finish location within the US and returns the driving route, cost-effective fuel stops along that route, and the additional fuel cost for a vehicle with a maximum range of 500 miles and fuel economy of 10 miles per gallon.
>
> I'll briefly explain the architecture, demonstrate the API in Postman, and then give a quick code walkthrough.

## 1. Architecture and key constraint — ~40 seconds

**Say:**

> The supplied fuel-price dataset contains many station records, and geocoding every station during an API request would create unnecessary external calls and latency.
>
> Instead, the fuel data is preprocessed during import. Station records are deduplicated and their coordinates are prepared from the bundled US cities data.
>
> At request time, the application resolves the endpoints locally where possible, makes the driving-route request to OSRM, and then performs station filtering and fuel optimization locally in memory.
>
> This keeps the external routing work to a minimum.

## 2. Live Postman demonstration — ~90 seconds

### 2.1 Long route

**Do:** Send the Los Angeles, CA → New York, NY request.

**Say:**

> Here I'm sending a coast-to-coast request using place names.

Scroll through the response.

> The API returns the route geometry, route distance, total additional fuel cost, and the recommended fuel stops.
>
> The exact values depend on the current OSRM route and fuel-price dataset, so I'm using the values returned by this live request rather than quoting hard-coded numbers.
>
> Each fuel stop includes the station details, price per gallon, gallons purchased, purchase cost, and mile marker along the route.

Show `meta`.

> The metadata also shows the number of stations considered, route points returned, corridor width, vehicle range, MPG, and server-side processing time.

### 2.2 Short route

**Do:** Send Oklahoma City, OK → Tulsa, OK.

**Say:**

> This demonstrates the full-tank assumption. The vehicle starts with a full 500-mile range, so if the route can be completed without buying additional fuel, no fuel stop is returned and the additional fuel cost is zero.
>
> In other words, `total_fuel_cost_usd` represents only fuel purchased during the journey. The initial tank is assumed to already be available at the origin.

### 2.3 Impossible route

**Do:** Send Honolulu, HI → Los Angeles, CA.

**Say:**

> This has no drivable road connection, so the API handles it with a 422 response instead of returning invalid route data.

### 2.4 Optional map

**Do:** Open `/map/`.

**Say:**

> I also included a simple Leaflet visualization for the route and selected fuel stops.

Skip this if time is tight.

## 3. Code walkthrough — ~100 seconds

### Point 1 — Data preprocessing

Open:

```text
routing/management/commands/import_fuel_prices.py
```

**Say:**

> The import command preprocesses the supplied fuel-price data. It deduplicates station records and prepares station coordinates before requests arrive, avoiding station-by-station geocoding on the request path.

Open:

```text
routing/views.py
```

**Say:**

> The view resolves the endpoints, requests the driving route from OSRM, finds nearby fuel stations locally, runs the fuel optimizer, and serializes the response.

### Point 2 — Route corridor matching

Open:

```text
routing/services/geo.py
```

**Say:**

> The route geometry is used to identify fuel stations within a configurable corridor. A KD-tree narrows the candidate stations efficiently, and the candidates are projected onto the route to obtain their mile markers.

### Point 3 — Fuel optimization

Open:

```text
routing/services/fuel.py
```

**Say:**

> The vehicle starts with a full 500-mile range. At 10 MPG, that corresponds to 50 gallons.
>
> The optimizer therefore calculates where additional fuel needs to be purchased. It looks ahead for reachable lower-priced stations and otherwise buys enough fuel to cover the required distance while respecting the maximum range.
>
> The returned cost represents only these additional purchases.

Show:

```text
routing/tests/test_fuel.py
```

**Say:**

> The fuel tests include comparisons against a brute-force reference implementation for randomized cases.

## 4. Testing — ~20 seconds

Run:

```bash
python manage.py check
python manage.py test
```

**Say:**

> The project includes Django checks and automated tests covering fuel optimization, route matching, location resolution, and the API view behavior.

Use the actual test count and result shown by the terminal. Do not state a hard-coded number unless it matches the current run.

## 5. Closing — ~20 seconds

**Say:**

> To summarize: the API accepts US locations, calculates a driving route, identifies fuel stations along the route, selects cost-effective refueling points while respecting the 500-mile range, and returns the additional fuel cost.
>
> The station data is preprocessed offline, routing calls are minimized, and the station matching and optimization work is performed locally.
>
> The repository includes the Django implementation, tests, setup instructions, Postman examples, and documentation.
>
> Thanks for watching.

## Quick recording checklist

- [ ] Django server is running.
- [ ] Fuel-price CSV has been imported.
- [ ] Postman collection is open.
- [ ] Long-route request is ready.
- [ ] Short-route request is ready.
- [ ] No-route request is ready.
- [ ] Editor is open to `routing/`.
- [ ] `python manage.py check` passes.
- [ ] `python manage.py test` passes.
- [ ] README is updated.
- [ ] Postman guide is updated.
- [ ] Use the current API output when describing actual results.
- [ ] Keep the final recording below 5 minutes.

## Important accuracy note

The normal request path is designed to minimize external calls. Endpoint resolution uses the bundled US cities data for supported place-name inputs, and the driving route is obtained from OSRM. In the Loom, describe the normal local-data path rather than claiming that every possible request always makes exactly one external call.
