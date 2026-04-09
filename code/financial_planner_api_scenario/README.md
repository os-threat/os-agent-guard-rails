# Financial Services Mini-App (v2)

This mini-app supports the financial services scenario with cross-product coverage:

- investments
- short-term savings
- superannuation
- insurance (general, household, death/life, business)
- communication and outreach workflows
- anniversaries and tax-planning checkpoints

## Runtime model

- Development: Windows
- Runtime: Docker Desktop (Linux containers)
- UI embedding target: iframe (OpenClaw localhost integration)

## Planned structure

```text
code/financial_planner_api_scenario/
  openapi/
  api/
    src/
      routes/
      services/
  db/
    mongo-init/
  package.json
  tests/
    api_smoke.mjs
    ui_smoke.mjs
    fixtures_api.mjs
    api_journey.mjs
  web/
    public/
    nginx/
```

## Startup (default)

From this directory:

```bash
docker compose up --build
```

**Operator runbook (first run, reset, demos, troubleshooting):** see [`RUNBOOK.md`](RUNBOOK.md).

Web UI:
- `http://localhost:8083/` (iframe-safe tabbed shell)

API:
- `http://localhost:8082/`
- `http://localhost:8082/admin/health`
- `http://localhost:8082/admin/integration-contract`
- **Swagger UI:** `http://localhost:8082/docs/` (OpenAPI: `http://localhost:8082/openapi.json`)
- **Same-origin via nginx (port 8083):** `http://localhost:8083/api/docs/`

In the web UI, open the **Help** tab for how to select records, use **Clear** for new rows, and run seeds.

## Configuration

Copy `.env.example` to `.env` and override as needed.

| Variable | Default | Purpose |
|---|---:|---|
| `API_PORT` | `8082` | API host port |
| `WEB_PORT` | `8083` | Web host port |
| `MONGO_PORT` | `27017` | Mongo host port |
| `MONGODB_URI` | `mongodb://mongo:27017/financial_services` | API-to-Mongo connection string |

## Reset

```bash
docker compose down -v
```

## Smoke tests

From `code/financial_planner_api_scenario/api`:

```bash
npm run test:api-smoke
npm run test:ui-smoke
```

## Scenario test suite

From `code/financial_planner_api_scenario`:

```bash
npm install
npm test
```

This runs OpenAPI lint (Spectral), fixture/API checks, and journey tests before smoke tests.

## Notes

- Rules management and decision engine logic are implemented in the OS Agent RPA Guardrails plugin, not this mini-app repository.
- This repository provides API/UI/data workflows and metadata hooks needed by the plugin.
- Web UI API base is configurable: default is same-origin `/api` when served by nginx on `:8083`; you can override with `?api=http://localhost:8082`.

## Troubleshooting

- If ports are in use, override `API_PORT`, `WEB_PORT`, or `MONGO_PORT` in `.env`.
- If healthchecks fail right after startup, wait for first dependency install in the API container and run `docker compose ps` again.
- To fully clean state: `docker compose down -v` then `docker compose up --build`.
- **Extended troubleshooting, demo mapping, and pre-demo checklist:** [`RUNBOOK.md`](RUNBOOK.md).
