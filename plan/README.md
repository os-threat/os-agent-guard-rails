# Plan documents — OS-Agent RPA Guard Rails

This folder holds **Stage 1** plans: how to implement the OpenClaw plugin/skill, how to build each dummy application, how to run end-user scenarios, and how to demo to investors. **Stage 2** code will live under `code/` (see overview).

## Index

| Document | Purpose |
|----------|---------|
| [rpa_guidelines_plan/PLAN.md](rpa_guidelines_plan/PLAN.md) | RPA Guard Rails plugin for OpenClaw: Layer A (shadow + `fun`), Layer B (promise graphs per [ch. 17 promise graphs](https://github.com/Volland/typedb-for-edge-ai-agents/blob/main/manuscript/17-promise-graphs.md)), dual MCP (Guard + Promise Graph), UI flows, testing, phased issues |
| [medical_app_scenario/PLAN.md](medical_app_scenario/PLAN.md) | Postgres + iframe UI mini-app: trial enrollment hyperedges, AE, reviews, hundreds of seed rows |
| [medical_app_scenario/SCENARIO.md](medical_app_scenario/SCENARIO.md) | Manual script: connect → **named rules MED-R01–R12** → **tasks M1–M6** (each defines SQL extract) → import on run → evaluate |
| [medical_app_scenario/DEMO.md](medical_app_scenario/DEMO.md) | Investor demos: 1 / 5 / 20 minutes |
| [financial_planner_api_scenario/PLAN.md](financial_planner_api_scenario/PLAN.md) | **Swagger/OpenAPI** mock + **MongoDB**, full docs + Swagger UI, REST shadow |
| [financial_planner_api_scenario/SCENARIO.md](financial_planner_api_scenario/SCENARIO.md) | **Named rules FP-R01–R12** → **tasks F1–F5** (each defines API extract) → import on run → HTTP RPA |
| [financial_planner_api_scenario/DEMO.md](financial_planner_api_scenario/DEMO.md) | Investor demos for API scenario |

**Canonical overview:** [a_seed/os-agent-guard-rails-overview.md](../a_seed/os-agent-guard-rails-overview.md) (deliverables, basic flow steps 1–11, Stage 1 vs Stage 2).

**Design background:** [agent_book/](../agent_book/) (source-and-scope, databases, TypeQL guardrails, PERA, MCP).

**TypeQL reference:** [skills/typedb/SKILL.md](../skills/typedb/SKILL.md).

---

## Setup (local investor / dev)

All scenarios assume **Windows with WSL 2** and **Docker Desktop**, services on **localhost** so OpenClaw can embed mini-apps in an iframe.

### Prerequisites

- WSL 2 distro (Ubuntu recommended), Docker Desktop with WSL integration enabled  
- **TypeDB** (version aligned with project when Stage 2 lands) — for shadow DB + promise graph  
- **Node.js** (LTS) — for mock API and plugin UI when implemented  
- **OpenClaw** — host for plugin/skill (Stage 2)

### What you run today (documentation only)

- Read `plan/rpa_guidelines_plan/PLAN.md` and scenario **PLAN / SCENARIO / DEMO** files.  
- No `docker compose` is required until **Stage 2** adds `code/medical_app_scenario` and `code/financial_planner_api_scenario`.

### What you will run in Stage 2 (summary)

1. **Medical:** from `code/medical_app_scenario`, `docker compose up` (Postgres + web app on documented ports, e.g. web `8081`, DB `5433`).  
2. **Financial:** from `code/financial_planner_api_scenario`, start mock server (e.g. port `8082`) + **MongoDB** from compose.  
3. **Plugin:** install `code/rpa_plugin_skill` into OpenClaw; point registration at SQL connection string or OpenAPI URL; ensure **Guard MCP** and **Promise Graph MCP** reach the same TypeDB deployment.

### Ports (illustrative — confirm in each **PLAN.md** when code exists)

| Service | Example port |
|---------|----------------|
| Medical web | 8081 |
| Medical Postgres | 5433 |
| Financial mock API | 8082 |
| Plugin UI | TBD (OpenClaw) |
| TypeDB | TBD |

---

## Naming note

The user-facing name **financial planner** scenario is implemented under **`financial_planner_api_scenario`** (REST/OpenAPI). There is no separate `financial_planner_scenario` folder; use the paths above.
