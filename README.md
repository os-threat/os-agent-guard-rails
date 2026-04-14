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
| [code/rpa_plugin_skill/README.md](code/rpa_plugin_skill/README.md) | **RPA plugin/skill** — local TypeDB dev stack (`dev/docker-compose.yml`), Layer C/B/A database model |

## External references

- [Promise graphs (manuscript ch. 17)](https://github.com/Volland/typedb-for-edge-ai-agents/blob/main/manuscript/17-promise-graphs.md) — Layer B orchestration model  
- [Hypergraphs — medical trial example](https://github.com/Volland/typedb-for-edge-ai-agents/blob/main/manuscript/13-hypergraphs.md#complete-medical-trial-example) — richness target for Scenario 1  

## Stage 2 code in this repo

| Location | Status |
|----------|--------|
| [code/medical_app_scenario/](code/medical_app_scenario/) | **Implemented:** Docker Postgres, schema/views, seed generator, Express API + web UI, DB/API/Playwright tests. See [code/medical_app_scenario/README.md](code/medical_app_scenario/README.md) for how to run and test. |
| [code/financial_planner_api_scenario/](code/financial_planner_api_scenario/) | **Implemented:** Docker Compose (MongoDB + Node mock), full OpenAPI spec, `/docs`, seed (`C-ALLOW` / `C-DENY` / `C-NON-ACC`), guard rules FP-R01–FP12 on recommendations/trades, static mini-app, unit + E2E + smoke tests. |
| [code/rpa_plugin_skill/](code/rpa_plugin_skill/) | TypeDB **3.8.3** dev compose, [TypeQL CI](code/rpa_plugin_skill/README.md#typeql-ci-local-and-github-actions) (`typeql_ci/`, [#40](https://github.com/os-threat/os-agent-guard-rails/issues/40), [#41](https://github.com/os-threat/os-agent-guard-rails/issues/41), [#42](https://github.com/os-threat/os-agent-guard-rails/issues/42), [#43](https://github.com/os-threat/os-agent-guard-rails/issues/43), [#44](https://github.com/os-threat/os-agent-guard-rails/issues/44), [#45](https://github.com/os-threat/os-agent-guard-rails/issues/45), [#46](https://github.com/os-threat/os-agent-guard-rails/issues/46), [#47](https://github.com/os-threat/os-agent-guard-rails/issues/47), [#48](https://github.com/os-threat/os-agent-guard-rails/issues/48), [#49](https://github.com/os-threat/os-agent-guard-rails/issues/49), [#50](https://github.com/os-threat/os-agent-guard-rails/issues/50), [#51](https://github.com/os-threat/os-agent-guard-rails/issues/51), [#52](https://github.com/os-threat/os-agent-guard-rails/issues/52), [#53](https://github.com/os-threat/os-agent-guard-rails/issues/53), [#54](https://github.com/os-threat/os-agent-guard-rails/issues/54), [#55](https://github.com/os-threat/os-agent-guard-rails/issues/55), [#56](https://github.com/os-threat/os-agent-guard-rails/issues/56)). |

Runnable Stage 2 apps: `code/medical_app_scenario/`, `code/financial_planner_api_scenario/` (GitHub issues **#11–#17** for the financial stack).












