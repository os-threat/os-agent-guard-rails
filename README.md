# OS-Agent RPA Guard Rails

Guard rails for OpenClaw RPA: business rules on a **shadow TypeDB** model (SQL or OpenAPI in), **TypeQL `fun`** for decisions, and a **promise graph** for orchestration and audit—so agents can automate high-stakes workflows with deniable/allowable actions and a full trail.

## Documentation

| Resource | Description |
|----------|-------------|
| [a_seed/os-agent-guard-rails-overview.md](a_seed/os-agent-guard-rails-overview.md) | Project overview, deliverables (Stage 1 docs vs Stage 2 code), basic plugin flow |
| [plan/README.md](plan/README.md) | Index of all plans, local setup summary, links to scenarios and demos |
| [plan/rpa_guidelines_plan/PLAN.md](plan/rpa_guidelines_plan/PLAN.md) | Implementation plan for the OpenClaw plugin/skill |
| [plan/medical_app_scenario/](plan/medical_app_scenario/) | Postgres medical mini-app plan, user scenario, investor demos |
| [plan/financial_planner_api_scenario/](plan/financial_planner_api_scenario/) | Swagger/OpenAPI + MongoDB financial planner plan, scenario, demos |
| [agent_book/](agent_book/) | Source notes on databases, TypeQL guardrails, PERA, MCP |
| [skills/typedb/SKILL.md](skills/typedb/SKILL.md) | TypeQL 3.8+ patterns for schema and transactions |

## External references

- [Promise graphs (manuscript ch. 17)](https://github.com/Volland/typedb-for-edge-ai-agents/blob/main/manuscript/17-promise-graphs.md) — Layer B orchestration model  
- [Hypergraphs — medical trial example](https://github.com/Volland/typedb-for-edge-ai-agents/blob/main/manuscript/13-hypergraphs.md#complete-medical-trial-example) — richness target for Scenario 1  

## Stage 2 (not in repo yet)

Planned code locations: `code/medical_app_scenario`, `code/financial_planner_api_scenario`, `code/rpa_plugin_skill` (see overview).
