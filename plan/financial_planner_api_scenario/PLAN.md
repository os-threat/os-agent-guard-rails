# Financial planner API — Build plan (`plan/financial_planner_api_scenario`)

**Purpose:** Dummy **Swagger-documented REST API + OpenAPI 3.x + mock server + MongoDB** for Scenario 2 (OpenAPI → TypeQL shadow path). **Stage 1** documentation; **Stage 2** implementation in `code/financial_planner_api_scenario` (per overview).

**Swagger requirement:** The OpenAPI document must be **complete**: every path has **summary**, **description**, **requestBody** schemas, **responses** (including error shapes), **parameters**, **tags**, and **examples** where helpful. Serve **Swagger UI** (or Redoc) from the mock server (e.g. `/docs`) so humans and the plugin can browse the same contract the shadow transpiler uses.

**Contrast with medical:** TypeDB shadow schema is driven from **OpenAPI/Swagger**, not SQL DDL. **HTTP** semantics: **idempotency keys**, **versioned** resources, **fee** and **regulatory** rules (not clinical).

**Commonality with medical:** **Layer A** shadow + **`fun`** + **Layer B** promise graph; iframe **mini-app UI**; **Docker Desktop** on WSL.

**Environment:** **WSL 2** + **Docker Desktop**; API + MongoDB on **localhost** for OpenClaw iframe.

---

## 1. Repository layout (Stage 2 target)

```
code/financial_planner_api_scenario/
  openapi/
    financial-planner.yaml          # OpenAPI 3.x — single source of truth; full docs
  mock/
    server.js                       # express + openapi-validator + Swagger UI at /docs
    package.json
  db/
    mongo-init/                     # optional JS or JSON seed for mongosh
  seed/
    generate_data.js                # or .py — writes to MongoDB
  docker-compose.yml                # Node mock + MongoDB
  tests/
    test_openapi_contract.sh
    test_rules.spec.ts
plan/financial_planner_api_scenario/
  PLAN.md
  SCENARIO.md
  DEMO.md
```

---

## 2. API surface (suggested)

**Base path:** `/v1` — version prefix for shadow mapping.

| Resource | Methods | Notes |
|----------|---------|--------|
| `/clients` | GET, POST | KYC tier, risk profile |
| `/clients/{id}` | GET, PATCH | |
| `/accounts` | GET, POST | type: IRA, taxable, 401k rollover |
| `/accounts/{id}/holdings` | GET, POST | symbol, quantity, cost basis |
| `/plans` | GET, POST | financial plan header |
| `/plans/{id}/goals` | GET, POST | target date, amount |
| `/recommendations` | POST | **Idempotency-Key** header — body: client, risk, horizon |
| `/trades` | POST | **preview** vs **execute** flag; idempotency |
| `/fees` | GET | schedule lookup |
| `/documents` | POST | disclosure acceptance record |

**Errors:** JSON Problem Details (`application/problem+json`); include `trace_id` for promise linking.

**Documentation:** Each operation document in YAML how it mutates or reads MongoDB collections so **SCENARIO.md** task extracts stay traceable to real routes.

---

## 3. Data volume (“few hundred documents” in MongoDB)

| Collection | Approx. documents |
|------------|---------------------|
| `clients` | ~50–80 |
| `accounts` | ~80–150 |
| `holdings` | ~200–400 |
| `plans` / `goals` | ~100–200 combined |
| `fee_schedules` / `disclosures` | ~20–40 |
| `trade_preview_audit` | ~100+ |

---

## 4. Web UI (iframe-friendly)

**Minimal SPA** (or static + fetch):

- **Dashboard** — client count, AUM rollup (mock), open recommendations.  
- **Client detail** — accounts, risk, KYC tier.  
- **Recommendation flow** — form → `POST /v1/recommendations` with `Idempotency-Key` → show response + **Guard** overlay when plugin is wired.  
- **Trade flow** — `POST /v1/trades` with `preview: true`, review, then `preview: false` / execute with same or linked idempotency policy per spec.

**Port (example):** `8082` — document in README.

---

## 5. OpenAPI → TypeQL shadow (plugin concern)

- **Register** OpenAPI URL (e.g. `http://localhost:8082/openapi.json` or static `financial-planner.yaml`) + base URL in plugin.  
- **Extract:** paths, methods, schemas, enums → **PERA** entities/relations (`http-request`, `resource`, `client`, `account`, …).  
- **`fun`:** See **SCENARIO.md** for the **named rule list** (suitability, concentration, KYC, fees, idempotency, wash-sale, IRA vs taxable, horizon, trace_id, etc.).

---

## 6. Docker

- **Services:** Node mock + **MongoDB** (`mongodb:latest` or pinned major).  
- **Health:** `GET /health` on mock; MongoDB healthcheck optional.  
- **Volumes:** named volume for MongoDB so re-seed is explicit (not silent).

---

## 7. Testing

- **Contract:** Dredd or schemathesis against `financial-planner.yaml`.  
- **Rules:** unit tests for **`fun`** inputs from sample JSON bodies (aligned with **SCENARIO.md** rules).  
- **E2E:** one **ALLOW** and one **DENY** recommendation path using seeded clients.

---

## 8. Disclaimer

Fictional financial data; **not** investment advice or a registered product.
