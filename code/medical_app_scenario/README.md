# Medical Mini App (Scenario 1)

This directory contains the Stage 2 implementation scaffold for the medical mini app described in `plan/medical_app_scenario/`.

## Development and runtime model

- Development is done on Windows in this repository.
- Runtime is Docker Desktop containers (WSL is optional for shell ergonomics).
- Services bind localhost for OpenClaw iframe demos.

## Quick start

1. Copy environment file:
   - PowerShell: `Copy-Item .env.example .env`
2. Start Postgres:
   - `docker compose up -d`
3. Check health:
   - `docker compose ps`
4. Apply schema:
   - PowerShell: `Get-Content db/schema.sql | docker compose exec -T postgres psql -U medical_app -d medical_mini_app -v ON_ERROR_STOP=1`
5. Apply views:
   - PowerShell: `Get-Content db/views.sql | docker compose exec -T postgres psql -U medical_app -d medical_mini_app -v ON_ERROR_STOP=1`
6. Start API server:
   - `cd web`
   - `npm install`
   - `node src/server.js`
7. Open UI:
   - `http://localhost:8081`

Optional pgAdmin:

- `docker compose --profile admin up -d`
- Open `http://localhost:5051`
- Login with `.env` values (`PGADMIN_DEFAULT_EMAIL` / `PGADMIN_DEFAULT_PASSWORD`)
- Add server in pgAdmin:
  - Host: `postgres`
  - Port: `5432`
  - Username: `POSTGRES_USER` from `.env`
  - Password: `POSTGRES_PASSWORD` from `.env`

Stop services:

- `docker compose down`

## Ports

- Web app + API: `8081`
- Postgres: `5433` (host) -> `5432` (container)
- pgAdmin (optional): `5051`

## Connection string (local development)

`postgresql://medical_app:medical_app_dev_pw@localhost:5433/medical_mini_app`

Use values from `.env` if customized.

## API endpoints (initial)

- `GET /health`
- `GET /patients?search=...`
- `GET /patients/:id`
- `GET /patients/:id/trial-guard` (active enrollments + pending review flag for MED-R06 UI)
- `GET /trials`
- `GET /trials/:id`
- `POST /enrollments`
- `PUT /enrollments/:id`
- `POST /prescriptions`
- `POST /adverse-events`
- `POST /enrollment-reviews`
- `PUT /enrollment-reviews/:id`
- `GET /dashboard` — counts for UI
- `GET /options` — dropdown data for forms
- `GET /enrollments`, `GET /enrollment-reviews`
- `POST /admin/reseed` — dev only; regenerates and loads seed SQL

## Testing

Run commands from **`code/medical_app_scenario`** unless noted. Postgres must be up and (for API/UI tests) seeded.

### Prerequisites

- Docker Desktop running; `docker compose up -d` brings up Postgres (and optional pgAdmin).
- **Python 3** for `seed/generate_data.py`.
- **Node.js** for API/UI and smoke tests.
- **`.env`** at `code/medical_app_scenario/.env` (copy from `.env.example`). The API reads `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `API_PORT` (default `8081`).

### One-shot: seed the database

From `code/medical_app_scenario`:

```powershell
python seed/generate_data.py
Get-Content seed/data.sql | docker compose exec -T postgres psql -U medical_app -d medical_mini_app -v ON_ERROR_STOP=1
```

This loads deterministic demo data (named cohorts per `plan/medical_app_scenario/PLAN.md` §2.1) and aligns sequences for API inserts.

### 1. DB assertions (`tests/test_db.sh`)

- **What it does:** Starts compose if needed, regenerates and loads `seed/data.sql`, then checks row floors and that key fixture names exist.
- **How to run:** Git Bash or WSL: `bash tests/test_db.sh` from `code/medical_app_scenario`.

### 2. API smoke (`web/tests/api-smoke.mjs`)

- **What it does:** Starts the Express app on an ephemeral port, hits `/health`, searches patients, creates an enrollment with **two** prescribers and **two** medications (junction rows verified in DB), and creates a prescription.
- **How to run** (after seeding):

```powershell
cd web
node tests/api-smoke.mjs
```

- **npm:** `cd web && npm test` runs the same via `test:api-smoke` (requires `node` on your PATH).

### 3. UI smoke (Playwright — `web/e2e/`)

- **What it does:** Opens the SPA, checks dashboard metrics load, verifies investor **M1** quick-pick and patient search for **Jordan Hayes**, and checks prescription **trial-related** controls and the MED-R06 banner.
- **First-time browser install:**

```powershell
cd web
npx playwright install chromium
```

- **How to run:**

```powershell
cd web
npx playwright test
```

`playwright.config.js` can start the API automatically (`webServer` → `node src/server.js`) and waits for `http://127.0.0.1:8081/health`.

- **Port 8081:** If something else is using **8081**, stop that process before running with a fresh server, or Playwright’s `webServer` step may fail. With `CI=1`, the config expects to bind a new server; free the port first.
- **`reuseExistingServer`:** When `CI` is unset, Playwright may reuse an already-running server on `8081` (useful if you started `node src/server.js` manually with the same code).

### Test scripts summary (`web/package.json`)

| Script | Purpose |
|--------|---------|
| `npm test` | API smoke (`test:api-smoke`) |
| `npm run test:e2e` | Playwright UI smoke |
| `npm run test:e2e:ui` | Playwright UI mode (interactive) |

### CI / local checklist

1. `docker compose up -d`
2. Apply `db/schema.sql` and `db/views.sql` if starting from an empty DB
3. Seed (commands above)
4. `cd web && node tests/api-smoke.mjs`
5. `cd web && npx playwright test` (after `npx playwright install chromium` once)

## Repository structure

- `db/` — schema and views
- `seed/` — deterministic demo data generator and generated SQL
- `web/` — API + static UI (`public/`), Playwright config and e2e tests
- `tests/` — shell DB assertions

## Data disclaimer

All medical data in this project is synthetic test data for demos and development. It is not clinical data and not for production healthcare use.
