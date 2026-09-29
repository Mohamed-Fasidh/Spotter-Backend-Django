**# Testing the Fuel Route API with Postman**

\> A step-by-step guide to exercising the Fuel Route API from Postman, including the exact requests, expected responses, validation checks, and edge cases.

**---**

**## 0. Prerequisites**

Start the Django server first.

**### macOS / Linux**

\`\`\`bash

source .venv/bin/activate

python manage.py migrate

python manage.py import_fuel_prices fuel-prices-for-be-assessment.csv

python manage.py runserver

\`\`\`

**### Windows PowerShell**

\`\`\`powershell

.\\.venv\Scripts\Activate.ps1

python manage.py migrate

python manage.py import_fuel_prices fuel-prices-for-be-assessment.csv

python manage.py runserver

\`\`\`

The server runs at:

\`\`\`text

http\://127.0.0.1:8000/

\`\`\`

\> **\*\*Keep the Django development server running while executing the Postman requests.\*\***

**---**

**## 1. One-Time Postman Setup**

**### 1.1 Create a Postman environment**

1\. Open **\*\*Postman\*\***.

2\. Go to **\*\*Environments\*\*** in the left sidebar.

3\. Click **\*\*+\*\*** to create an environment.

4\. Name it:

   \`\`\`text

   Fuel Route (local)

   \`\`\`

5\. Add the following variable:

   | Variable | Initial / Current Value |

   |---|---|

   | \`base_url\` | \`http\://127.0.0.1:8000\` |

6\. Click **\*\*Save\*\***.

7\. Select **\*\*Fuel Route (local)\*\*** from the environment dropdown.

You can now use:

\`\`\`text

{{base_url}}

\`\`\`

instead of repeatedly entering the local server URL.

**### 1.2 Create a collection**

1\. Go to **\*\*Collections\*\***.

2\. Click **\*\*+\*\***.

3\. Name the collection:

   \`\`\`text

   Fuel Route API

   \`\`\`

4\. Add the requests described below.

\> **\*\*Tip:\*\*** All API requests are \`GET\` requests. The API is intentionally read-only.

**---**

**## 2. API Requests**

For each request:

1\. Set the HTTP method to **\*\*GET\*\***.

2\. Enter the URL.

3\. Use the **\*\*Params\*\*** tab for query parameters.

4\. Click **\*\*Send\*\***.

Using the **\*\*Params\*\*** tab allows Postman to handle URL encoding for spaces and commas automatically.

**---**

**### 2.1 API Documentation — HTML**

**\*\*Method\*\***

\`\`\`text

GET

\`\`\`

**\*\*URL\*\***

\`\`\`text

{{base_url}}/

\`\`\`

**\*\*Expected response\*\***

\`\`\`text

200 OK

\`\`\`

The response is an HTML documentation page.

Select **\*\*Preview\*\*** in Postman's response pane to view the rendered documentation.

**---**

**### 2.2 Machine-Readable API Specification — JSON**

**\*\*Method\*\***

\`\`\`text

GET

\`\`\`

**\*\*URL\*\***

\`\`\`text

{{base_url}}/api/

\`\`\`

**\*\*Expected response\*\***

\`\`\`text

200 OK

\`\`\`

The response contains machine-readable information about:

\- Available endpoints

\- Query parameters

\- Status codes

\- Vehicle assumptions

\- API behavior

**---**

**### 2.3 Long Route — Los Angeles to New York**

\> **\*\*Primary demonstration request\*\***

This request demonstrates the main assessment requirement: routing over a long distance while selecting multiple fuel stops within the vehicle's 500-mile range.

**\*\*Method\*\***

\`\`\`text

GET

\`\`\`

**\*\*URL\*\***

\`\`\`text

{{base_url}}/route/

\`\`\`

**\*\*Params\*\***

\| Key | Value |

\|---|---|

\| \`start\` | \`Los Angeles, CA\` |

\| \`finish\` | \`New York, NY\` |

Postman will construct the equivalent query string:

\`\`\`text

{{base_url}}/route/?start=Los%20Angeles%2C%20CA&finish=New%20York%2C%20NY

\`\`\`

**\*\*Expected response\*\***

\`\`\`text

200 OK

\`\`\`

**### Example values from the current local test**

\`\`\`text

distance_miles            ≈ 2793.4


total_fuel_cost_usd       = cost of additional fuel purchased

\`\`\`

The response contains an ordered \`fuel_stops\` array.

Each selected station contains information such as:

\`\`\`json

{

  "name": "Maverik #674",

  "city": "North Las Vegas",

  "state": "NV",

  "lat": 36.19886,

  "lng": -115.1175,

  "price_per_gallon": 3.2823,

  "gallons": 26.09,

  "cost_usd": 85.63,

  "mile_marker": 260.9

}

\`\`\`

**### What to verify**

Check that:

\- \`distance_miles\` is reasonable for the requested route.

\- \`fuel_stops\` is ordered by \`mile_marker\`.

\- Each consecutive fuel-stop leg is within the \`500-mile\` vehicle range.

\- The initial leg from the origin to the first fuel stop is within \`500 miles\`.

\- The final leg from the last fuel stop to the destination is within \`500 miles\`.

\- \`price_per_gallon\` comes from the imported fuel-price dataset.

\- \`total_fuel_cost_usd\` includes the initial full-tank cost and subsequent fuel purchases.

\- \`meta.elapsed_ms\` reports the server-side processing time.

\> **\*\*Important:\*\*** The exact distance, station selection, prices, and elapsed time can vary with the routing response and imported dataset. Use the values above as a reference from the current local test, not as hard-coded API guarantees.

**---**

**### 2.4 Long Route by Raw Coordinates**

This request exercises the coordinate-input path and avoids endpoint geocoding.

**\*\*Method\*\***

\`\`\`text

GET

\`\`\`

**\*\*URL\*\***

\`\`\`text

{{base_url}}/route/

\`\`\`

**\*\*Params\*\***

\| Key | Value |

\|---|---|

\| \`start\` | \`34.05,-118.24\` |

\| \`finish\` | \`40.71,-74.01\` |

**\*\*Expected response\*\***

\`\`\`text

200 OK

\`\`\`

The route should be broadly equivalent to the Los Angeles → New York place-name request.

**### What to verify**

\- Coordinates are parsed directly.

\- No endpoint place-name geocoding is required.

\- A valid driving route is returned.

\- Fuel stops remain ordered.

\- No route leg exceeds the configured 500-mile range.

**---**

**### 2.5 Short Route Within One Tank**

This is an important edge-case test.

**\*\*Method\*\***

\`\`\`text

GET

\`\`\`

**\*\*URL\*\***

\`\`\`text

{{base_url}}/route/

\`\`\`

**\*\*Params\*\***

\| Key | Value |

\|---|---|

\| \`start\` | \`Oklahoma City, OK\` |

\| \`finish\` | \`Tulsa, OK\` |

**\*\*Current local test result\*\***

\`\`\`text

distance_miles           ≈ 106.3


total_fuel_cost_usd      = 0.00 (when no additional fuel is purchased)

fuel_stops               = []

\`\`\`

**\*\*Expected response\*\***

\`\`\`text

200 OK

\`\`\`

**### Why there are no fuel stops**

The vehicle has:

\`\`\`text

Maximum range = 500 miles

Fuel economy  = 10 MPG

Tank capacity = 50 gallons

\`\`\`

The route is only approximately:

\`\`\`text

106.3 miles

\`\`\`

Therefore, the vehicle can complete the trip without purchasing additional fuel.

**### Important fuel-cost behavior**

\> **\*\*No fuel stop does not mean zero fuel cost.\*\***

The vehicle still consumes:

\`\`\`text

106.3 / 10 = 10.63 gallons

\`\`\`

The current implementation includes the initial full-tank cost in:

\`\`\`text

total_fuel_cost_usd

\`\`\`

Therefore, \`fuel_stops\` can correctly be an empty array while \`total_fuel_cost_usd\` remains non-zero.

**---**

**### 2.6 No Drivable Route — 422**

This tests an impossible road connection.

**\*\*Method\*\***

\`\`\`text

GET

\`\`\`

**\*\*URL\*\***

\`\`\`text

{{base_url}}/route/

\`\`\`

**\*\*Params\*\***

\| Key | Value |

\|---|---|

\| \`start\` | \`Honolulu, HI\` |

\| \`finish\` | \`Los Angeles, CA\` |

**\*\*Expected response\*\***

\`\`\`text

422 Unprocessable Entity

\`\`\`

Example response:

\`\`\`json

{

  "error": "Impossible route between points"

}

\`\`\`

There is no drivable road route across the ocean, so the API returns a controlled error instead of crashing.

**---**

**### 2.7 Missing Input — 400**

This verifies input validation.

**\*\*Method\*\***

\`\`\`text

GET

\`\`\`

**\*\*URL\*\***

\`\`\`text

{{base_url}}/route/

\`\`\`

**\*\*Params\*\***

\| Key | Value |

\|---|---|

\| \`start\` | *\*(empty)\** |

\| \`finish\` | \`Tulsa, OK\` |

**\*\*Expected response\*\***

\`\`\`text

400 Bad Request

\`\`\`

Example:

\`\`\`json

{

  "error": "Missing start/finish value."

}

\`\`\`

**---**

**### 2.8 Unresolvable Location — 400**

This verifies geocoding failure handling.

**\*\*Method\*\***

\`\`\`text

GET

\`\`\`

**\*\*URL\*\***

\`\`\`text

{{base_url}}/route/

\`\`\`

**\*\*Params\*\***

\| Key | Value |

\|---|---|

\| \`start\` | \`asdkjhaskdjh\` |

\| \`finish\` | \`Tulsa, OK\` |

**\*\*Expected response\*\***

\`\`\`text

400 Bad Request

\`\`\`

Example:

\`\`\`json

{

  "error": "Could not geocode location: ..."

}

\`\`\`

The exact error detail may vary.

**---**

**## 3. Automated Postman Tests**

Postman can validate the response automatically after each request.

**### 3.1 Long-route assertions**

Open request **\*\*2.3\*\***, select the **\*\*Tests\*\*** tab, and add:

\`\`\`javascript

pm.test("status is 200", () => {

    pm.response.to.have.status(200);

});

const body = pm.response.json();

pm.test("has route, distance, cost, and stops", () => {

    pm.expect(body).to.have.property("route");

    pm.expect(body).to.have.property("distance_miles");

    pm.expect(body).to.have.property("total_fuel_cost_usd");

    pm.expect(body).to.have.property("fuel_stops");

    pm.expect(body.fuel_stops).to.be.an("array");

});

pm.test("fuel stops are ordered and every leg is reachable", () => {

    const marks = [

        0,

        ...body.fuel_stops.map(stop => stop.mile_marker),

        body.distance_miles

    ];

    for (let i = 1; i < marks.length; i++) {

        pm.expect(marks[i]).to.be.at.least(marks[i - 1]);

        pm.expect(marks[i] - marks[i - 1]).to.be.at.most(500 + 1e-6);

    }

});

\`\`\`

This checks the core 500-mile constraint automatically.

**### 3.2 No-route assertions**

For request **\*\*2.6\*\***, use:

\`\`\`javascript

pm.test("status is 422", () => {

    pm.response.to.have.status(422);

});

pm.test("has an error message", () => {

    pm.expect(pm.response.json()).to.have.property("error");

});

\`\`\`

**---**

**## 4. Run the Entire Collection**

After adding the requests and tests:

1\. Hover over the **\*\*Fuel Route API\*\*** collection.

2\. Click **\*\*Run\*\***.

3\. Select all requests.

4\. Click **\*\*Run Fuel Route API\*\***.

5\. Review the pass/fail results.

The Collection Runner provides a single regression run for the documented API scenarios.

\> **\*\*Recommended assessment demo:\*\*** Run the long route, short route, and no-route cases during the Loom recording. Together they demonstrate the main optimization path and two important edge cases.

**---**

**## 5. What the Reviewer Should See**

The Postman demonstration should establish the following:

\| Scenario | Expected behavior |

\|---|---|

\| Long route | Route returned with multiple optimized fuel stops |

\| Coordinate input | Route works without place-name endpoint geocoding |

\| Short route | \`fuel_stops = []\`, but total fuel cost remains non-zero |

\| Impossible route | Controlled \`422\` response |

\| Missing parameter | Controlled \`400\` response |

\| Invalid location | Controlled \`400\` response |

**### Core correctness checks**

For a valid route:

\`\`\`text

Origin

   │

   ├── ≤ 500 miles ──► Fuel Stop 1

   │

   ├── ≤ 500 miles ──► Fuel Stop 2

   │

   ├── ≤ 500 miles ──► ...

   │

   └── ≤ 500 miles ──► Destination

\`\`\`

The fuel-stop \`mile_marker\` values should increase monotonically, and every consecutive leg must remain within the vehicle's maximum range.

**---**

**## 6. Performance and External API Notes**

**### Routing API calls**

The application is designed to minimize external routing requests.

The normal flow is:

\`\`\`text

Start / Finish

      │

      ▼

Offline city lookup

      │

      ├── Found ──────────────┐

      │                       │

      └── Missing → Nominatim │

                              ▼

                         OSRM route

                              │

                              ▼

                    Local station filtering

                              │

                              ▼

                       Fuel optimization

\`\`\`

The route calculation uses one OSRM routing request for the normal uncached route path.

Repeated identical requests can benefit from application-level caching.

**### Response time**

Observed local test results:

\| Test | Observed \`elapsed_ms\` |

\|---|---:|

\| Los Angeles → New York | \`215.3 ms\` |

\| Oklahoma City → Tulsa | \`828.5 ms\` |

\> These values are local observations, not latency guarantees. Public routing and geocoding services can introduce variable network latency.

**---**

**## 7. Response Size and Geometry**

By default, the API returns simplified route geometry.

The route is reduced to approximately:

\`\`\`text

600 points

\`\`\`

This keeps the JSON response compact and easier to inspect in Postman.

If the API supports:

\`\`\`text

&geometry=full

\`\`\`

the response can contain substantially more route points.

\> **\*\*Postman note:\*\*** A large full-geometry response may not render in Postman's table view. Use **\*\*Pretty → JSON\*\*** to inspect the raw response. This does not indicate an API failure.

**---**

**## 8. HTTP Method**

The route API is read-only and uses:

\`\`\`text

GET /route/

\`\`\`

Sending:

\`\`\`text

POST /route/

\`\`\`

should return:

\`\`\`text

405 Method Not Allowed

\`\`\`

**---**

**## 9. Public Routing Service Availability**

The API uses the public OSRM demo server for routing.

If the public routing service is temporarily unavailable or rate-limited, the API can return:

\`\`\`text

502 Bad Gateway

\`\`\`

This is an external-service failure rather than an application-level route-validation failure.

For production deployment, a self-hosted OSRM instance would provide greater control over availability and rate limits.

**---**

**## 10. Recommended 5-Minute Loom Flow**

Use this sequence for the assessment video:

**### 1. Quick project overview — \~30 seconds**

Show:

\`\`\`text

Django

   ↓

Location resolution

   ↓

OSRM routing

   ↓

Route corridor filtering

   ↓

Fuel optimization

   ↓

JSON response

\`\`\`

**### 2. Show the main endpoint — \~60 seconds**

Run:

\`\`\`text

Los Angeles, CA

        ↓

New York, NY

\`\`\`

Point out:

\- Route distance

\- Fuel stops

\- Fuel prices

\- Mile markers

\- Total fuel cost

\- 500-mile constraint

**### 3. Explain the optimization — \~60 seconds**

Explain:

\> The vehicle has a 500-mile maximum range and achieves 10 MPG. Stations are filtered to a corridor around the route, ordered by route position, and the optimizer prefers cheaper reachable stations while ensuring every route leg remains within the vehicle's range.

**### 4. Demonstrate the short route — \~45 seconds**

Run:

\`\`\`text

Oklahoma City, OK

        ↓

Tulsa, OK

\`\`\`

Show:

\`\`\`text

distance ≈ 106.3 miles

fuel_stops = []

total_fuel_cost_usd = 0 when no additional fuel is purchased

\`\`\`

Explain:

\> No additional fuel purchase is required. The vehicle consumes fuel from its initial full tank, so the reported additional fuel purchase cost is zero.

**### 5. Demonstrate error handling — \~45 seconds**

Run:

\`\`\`text

Honolulu, HI

        ↓

Los Angeles, CA

\`\`\`

Show:

\`\`\`text

422 Unprocessable Entity

\`\`\`

**### 6. Show the code — \~45 seconds**

Briefly show:

\- Django project structure

\- Fuel-price import command

\- Routing service

\- Station filtering

\- Fuel optimizer

\- Tests

**### 7. Show tests — \~15 seconds**

Run:

\`\`\`bash

python manage.py test

\`\`\`

Expected:

\`\`\`text

Ran 16 tests

OK

\`\`\`

**---**

**## Fuel-Cost Model

The vehicle starts the journey with a full tank.

```text
Maximum range = 500 miles
Fuel economy  = 10 MPG
Initial tank  = 50 gallons
```

The API's `total_fuel_cost_usd` represents **only additional fuel purchased during the journey**.

It does **not** include the monetary value of fuel already present in the initial full tank.

Therefore:

- A 100-mile route that fits within the initial tank can return `fuel_stops: []` and `total_fuel_cost_usd: 0.00`.
- A longer route can return one or more fuel stops and a total equal to the sum of those actual purchases.
- Do not add a separate starting-fuel cost to the API total.

---

## 11. Final Postman Checklist**

Before recording the Loom, verify:

\- [ ] Django server is running.

\- [ ] Fuel-price CSV has been imported.

\- [ ] \`GET /\` returns API documentation.

\- [ ] \`GET /api/\` returns the machine-readable specification.

\- [ ] Los Angeles → New York returns \`200\`.

\- [ ] Multiple fuel stops are returned for the long route.

\- [ ] Fuel-stop mile markers are ordered.

\- [ ] No route leg exceeds \`500 miles\`.

\- [ ] Oklahoma City → Tulsa returns \`200\`.

\- [ ] Short route returns \`fuel_stops: []\`.

\- [ ] Short route reports zero additional fuel cost when no refueling purchase is required.

\- [ ] Honolulu → Los Angeles returns \`422\`.

\- [ ] Missing input returns \`400\`.

\- [ ] Invalid location returns \`400\`.

\- [ ] Postman automated assertions pass.

\- [ ] \`python manage.py test\` reports all tests passing.

**---**

\> **\*\*Assessment-ready result:\*\*** The Postman collection demonstrates the primary route-optimization workflow, the 500-mile vehicle constraint, total fuel-cost calculation, coordinate input, and controlled error handling without requiring unnecessary external routing calls.