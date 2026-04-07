# Financial planner mini-app (OpenAPI + MongoDB)

Dummy REST API and iframe-friendly UI for OS-Agent Guard Rails demos. **Not** investment advice.

## Ports and URLs

| Service | Default |
|---------|---------|
| Mock API + Swagger UI + mini-app | `http://localhost:8082` |
| OpenAPI JSON | `http://localhost:8082/openapi.json` |
| Swagger UI | `http://localhost:8082/docs` |
| Health | `http://localhost:8082/health` |
| MongoDB (host) | `localhost:27017` |

## Run with Docker Desktop (Linux containers)

From this directory:

```bash
docker compose up --build
```

- **Windows:** Docker Desktop with WSL2 backend; maps **8082** and **27017** to the host.
- **Named volume** `fp-mini-mongo-data` persists MongoDB data. To **re-seed** from scratch:  
  `docker compose down -v` then `docker compose up --build` (or run `npm run seed` from `mock/` against a fresh DB).

`AUTO_SEED` defaults to `true` in Compose so the API loads demo data on startup.

## Local development (Windows)

1. Install **Node.js 20+** and **MongoDB** (or run only Mongo in Docker: `docker compose up mongo`).
2. `cd mock && npm install`  
   On Windows, if install fails on a postinstall script, use `npm install` in the same shell where `node` is on `PATH`, or rely on the checked-in `mock/.npmrc` (`ignore-scripts=true`).
3. Set `MONGODB_URI=mongodb://127.0.0.1:27017/financial_planner` (or your port).
4. From repo root of this scenario: `node seed/generate_data.js`
5. `npm start` (or `npm run dev`)

## Layout

| Path | Role |
|------|------|
| `openapi/financial-planner.yaml` | OpenAPI 3.x contract |
| `mock/` | Express server |
| `seed/generate_data.js` | MongoDB seed (`C-ALLOW`, `C-DENY`, `C-NON-ACC`, …) |
| `web/public/` | Static mini-app (served at `/`) |
| `tests/` | Rules unit tests, E2E, Dredd hooks |

## API prefix

All business routes are under **`/v1`**. See `plan/financial_planner_api_scenario/` for scenario docs.
