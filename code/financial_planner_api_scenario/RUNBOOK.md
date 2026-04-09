# Financial Services Mini-App — Operator runbook (issue #34)

This document is the **release-readiness and operations guide** for `code/financial_planner_api_scenario`. It complements [`README.md`](README.md) and maps investor demos to concrete URLs and data.

**Canonical scenario docs:** `plan/financial_planner_api_scenario/` (`PLAN.md`, `SCENARIO.md`, `DEMO.md`).

---

## 1. Prerequisites (Windows + Docker Desktop)

1. **Docker Desktop** installed and running (Linux container mode).
2. **WSL 2** optional; PowerShell or cmd is sufficient if Docker Desktop is healthy.
3. **Ports free** on the host (defaults):
   - `8082` — API
   - `8083` — static web UI (nginx)
   - `27017` — MongoDB (host mapping)

---

## 2. First run from zero

```powershell
cd code\financial_planner_api_scenario
copy .env.example .env
docker compose up --build
```

Wait until all services are **healthy**:

```powershell
docker compose ps
```

### Quick verification

| Check | URL or command |
|-------|------------------|
| API health | `GET http://localhost:8082/admin/health` |
| Integration contract | `GET http://localhost:8082/admin/integration-contract` |
| Web UI | Open `http://localhost:8083/` in a browser |
| OpenAPI file (on disk) | `openapi/financial-services.yaml` |

### Load data (recommended before demos)

1. **Rich synthetic dataset** (volume + variety):

   ```http
   POST http://localhost:8082/admin/jobs/seed
   ```

   Or use **Admin** tab in the UI → **Run Rich Seed**.

2. **Deterministic demo fixtures** (named clients for scripted demos):

   ```http
   POST http://localhost:8082/admin/jobs/seed-fixtures
   ```

   Or **Admin** tab → **Run Fixture Seed**.

**Fixture client IDs** (for `DEMO.md` / `SCENARIO.md` narratives):

| Cohort | Client ID |
|--------|-----------|
| Renewal / anniversary | `C-FIX-RENEWAL` |
| Tax pre-window | `C-FIX-TAX` |
| Campaign / social opt-in | `C-FIX-CAMPAIGN` |
| Complaint holdout | `C-FIX-COMPLAINT` |

Verify fixtures:

```http
GET http://localhost:8082/v1/clients/C-FIX-RENEWAL
```

---

## 3. Full reset (clean slate)

Removes containers **and** the MongoDB named volume (all app data):

```powershell
cd code\financial_planner_api_scenario
docker compose down -v
docker compose up --build
```

Then re-run seed steps in §2.

---

## 4. Smoke tests (post-deploy)

From `code/financial_planner_api_scenario/api` (requires Node on PATH; e.g. `C:\nvm4w\nodejs\node.exe`):

```powershell
npm install
npm run test:api-smoke
npm run test:ui-smoke
```

**Expect:** `api_smoke: ok` and `ui_smoke: ok`.

**Requires:** stack up (`docker compose up`) so `localhost:8082` and `localhost:8083` respond.

---

## 5. Troubleshooting

### Ports already in use

Edit `.env` (from `.env.example`):

- `API_PORT`, `WEB_PORT`, `MONGO_PORT`

Then `docker compose up --build` again.

### API container `unhealthy` briefly

The API service runs `npm install` on first start when using a bind-mounted `api/` folder. Wait 30–60 seconds and run:

```powershell
docker compose ps
docker logs financial-v2-api
```

### MongoDB not ready

```powershell
docker logs financial-v2-mongo
```

Ensure `financial-v2-mongo` is **healthy** before the API marks healthy.

### Web UI shows “API unavailable”

- Confirm API: `http://localhost:8082/admin/health`
- The browser UI uses `API_BASE = http://localhost:8082` in `web/public/app.js`. If you embed the UI in another origin, you may need CORS or a reverse proxy; for localhost iframe demos, same-machine `localhost` is the supported path.

### `docker compose` errors on Windows

- Ensure Docker Desktop is **started** (whale icon stable).
- Try **Restart Docker Desktop** after hyper-v / WSL updates.

---

## 6. Logs and inspection

```powershell
docker logs financial-v2-api --tail 200
docker logs financial-v2-web --tail 100
docker logs financial-v2-mongo --tail 100
```

---

## 7. Demo runbook (maps to `plan/financial_planner_api_scenario/DEMO.md`)

**Base URLs**

- UI: `http://localhost:8083/`
- API: `http://localhost:8082/`

### 1-minute demo (DEMO §1-minute)

| DEMO step | Operator action |
|-----------|------------------|
| Dashboard + anniversaries | UI → **Dashboard** tab |
| Mixed client | UI → **Clients** tab, or open `GET /v1/clients/C-FIX-RENEWAL` |
| Renewal / anniversary story | After fixture seed: **Insurance** / **Tasks** tabs; renewal data tied to `C-FIX-RENEWAL` |
| Rule hit + `trace_id` | **Plugin** demonstrates rules; API errors use `application/problem+json` with `trace_id` where applicable |

### 5-minute demo (DEMO §5-minute)

| Minute block | Operator action |
|--------------|------------------|
| Architecture | Narrate OpenAPI → plugin shadow; point at `openapi/financial-services.yaml` |
| UI tabs | Walk **Dashboard**, **Admin**, **Clients**, **Superannuation**, **Insurance**, **Communications**, **Tasks** |
| “Client 360” style | Use **Clients** + related tabs; cross-check `GET /v1/clients/{id}` in Swagger or curl if desired |
| Admin / seed | **Admin** → seed buttons if you need a fresh population |

### 20-minute demo (DEMO §20-minute)

Follow DEMO blocks; use **Admin** for job/audit narrative:

- `GET /admin/jobs`
- `GET /admin/audit`

Use fixture IDs for deterministic stories (renewal, tax, campaign, complaint).

---

## 8. Plugin registration (reference only)

- **OpenAPI:** serve or register `openapi/financial-services.yaml` (or future `/openapi.json` if exposed).
- **Base URL:** `http://localhost:8082` (or host-adjusted).
- **Correlation:** send `x-correlation-id` on requests; responses include `_meta.correlation_id` on JSON bodies. See `GET /admin/integration-contract`.

**Out of scope for this repo:** rule authoring, decision engine, TypeQL `fun` — handled by OS Agent RPA Guardrails plugin.

---

## 9. Pre-demo checklist (5 minutes)

- [ ] `docker compose ps` — all services healthy  
- [ ] `GET /admin/health` — 200  
- [ ] `http://localhost:8083/` — loads tabs  
- [ ] Rich seed + fixture seed run if you need full volume + named demos  
- [ ] Spot-check `GET /v1/clients/C-FIX-RENEWAL`  
- [ ] `npm run test:api-smoke` and `npm run test:ui-smoke` (optional but recommended)

---

## 10. Disclaimer

All data is **fictional**. Not financial, tax, or insurance advice.
