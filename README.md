# OS-Agent RPA Guard Rails

Guard rails for OpenClaw RPA: business rules on a **shadow TypeDB** model (SQL or OpenAPI in), **TypeQL `fun`** for decisions, and a **promise graph** for orchestration and audit—so agents can automate high-stakes workflows with deniable/allowable actions and a full trail.

## Documentation

| Resource | Description |
|----------|-------------|
| [a_seed/os-agent-guard-rails-overview.md](a_seed/os-agent-guard-rails-overview.md) | Project overview, deliverables (Stage 1 docs vs Stage 2 code), basic plugin flow |
| [plan/README.md](plan/README.md) | Index of all plans, local setup summary, links to scenarios and demos |
| [plan/rpa_guidelines_plan/PLAN.md](plan/rpa_guidelines_plan/PLAN.md) | Implementation plan for the OpenClaw plugin/skill |
| [plan/medical_app_scenario/](plan/medical_app_scenario/) | Postgres medical mini-app plan, user scenario, investor demos |
| [code/medical_app_scenario/README.md](code/medical_app_scenario/README.md) | **Medical mini-app** — run, API, UI, **testing** (DB / API / Playwright) |
| [plan/financial_planner_api_scenario/](plan/financial_planner_api_scenario/) | Swagger/OpenAPI + MongoDB financial planner plan, scenario, demos |
| [code/financial_planner_api_scenario/README.md](code/financial_planner_api_scenario/README.md) | **Financial planner mini-app** — Docker (MongoDB + API), OpenAPI, seed data, iframe UI, tests |
| [agent_book/](agent_book/) | Source notes on databases, TypeQL guardrails, PERA, MCP |
| [skills/typedb/SKILL.md](skills/typedb/SKILL.md) | TypeQL 3.8+ patterns for schema and transactions |

## External references

- [Promise graphs (manuscript ch. 17)](https://github.com/Volland/typedb-for-edge-ai-agents/blob/main/manuscript/17-promise-graphs.md) — Layer B orchestration model  
- [Hypergraphs — medical trial example](https://github.com/Volland/typedb-for-edge-ai-agents/blob/main/manuscript/13-hypergraphs.md#complete-medical-trial-example) — richness target for Scenario 1  

## Stage 2 code in this repo

| Location | Status |
|----------|--------|
| [code/medical_app_scenario/](code/medical_app_scenario/) | **Implemented:** Docker Postgres, schema/views, seed generator, Express API + web UI, DB/API/Playwright tests. See [code/medical_app_scenario/README.md](code/medical_app_scenario/README.md) for how to run and test. |
| [code/financial_planner_api_scenario/](code/financial_planner_api_scenario/) | **Implemented:** Docker Compose (MongoDB + Node mock), full OpenAPI spec, `/docs`, seed (`C-ALLOW` / `C-DENY` / `C-NON-ACC`), guard rules FP-R01–FP12 on recommendations/trades, static mini-app, unit + E2E + smoke tests. |
| `code/rpa_plugin_skill` | Planned (see overview). |

Runnable Stage 2 apps: `code/medical_app_scenario/`, `code/financial_planner_api_scenario/` (GitHub issues **#11–#17** for the financial stack).
