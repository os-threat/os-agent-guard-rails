#!/usr/bin/env python3
"""
One-time helper: create RPA plugin GitHub issues on os-threat/os-agent-guard-rails.
Run from repo root: py scripts/create_rpa_github_issues.py

Requires: GitHub CLI (gh) on PATH or at %ProgramFiles%\\GitHub CLI\\gh.exe
"""
from __future__ import annotations

import os
import subprocess
import sys

REPO = "os-threat/os-agent-guard-rails"
LABEL = "enhancement"

# Full path to gh on Windows if not on PATH
def gh_exe() -> str:
    p = os.environ.get("ProgramFiles", r"C:\Program Files")
    candidate = os.path.join(p, "GitHub CLI", "gh.exe")
    if os.path.isfile(candidate):
        return candidate
    return "gh"


def create_issue(title: str, body: str) -> None:
    proc = subprocess.run(
        [
            gh_exe(),
            "issue",
            "create",
            "--repo",
            REPO,
            "--title",
            title,
            "--body",
            body,
            "--label",
            LABEL,
        ],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout, file=sys.stderr)
        sys.exit(proc.returncode)
    print(proc.stdout.strip())


ISSUES: list[tuple[str, str]] = [
    (
        "[RPA plugin] 0.1 — Local dev stack (Docker / WSL2)",
        """## Milestone
M0 Foundations

## Architecture context
- **Single TypeDB instance** on **Docker Desktop** (Windows); **logical databases** on that instance: **Layer C**, **Layer B**, and **one Layer A database per registered** SQL/API app (see `plan/rpa_guidelines_plan/PLAN.md`).
- Normative **TypeQL**: `skills/typedb/SKILL.md` (TypeDB 3.8+).

## Summary
Document and script local development: **TypeDB 3.8+** container, optional Postgres for SQL-path smoke tests later, **localhost** ports documented for plugin UI + OpenClaw.

## Acceptance criteria
- [ ] `docker compose` (or equivalent) brings up **TypeDB** with a pinned **3.8.x** image and **health** check documented
- [ ] README or dev doc describes **Windows + Docker Desktop** and optional **WSL2** shell for compose
- [ ] Document **server address** (e.g. `localhost:1729`) and that **multiple named databases** will be created on this **one instance** (C, B, A per app)
- [ ] Cross-link `plan/rpa_guidelines_plan/PLAN.md` §6 (integration / testing approach)

## References
- `plan/rpa_guidelines_plan/PLAN.md`
- `skills/typedb/SKILL.md`
""",
    ),
    (
        "[RPA plugin] 0.2 — CI: TypeQL validation (per skills/typedb/SKILL.md)",
        """## Milestone
M0 Foundations

## Summary
Add CI pipeline step that validates **TypeQL** against TypeDB **3.8+** conventions in `skills/typedb/SKILL.md`: correct **transaction type** (`schema` / `write` / `read`), **semicolon-terminated** queries, valid **`define` / `redefine`**, **entity / relation / attribute** roots (not `thing`), etc.

## Acceptance criteria
- [ ] Invalid TypeQL fails CI with a clear error
- [ ] Contributors can run the **same check locally** (documented in README or `plan/`)
- [ ] Doc explicitly references **`skills/typedb/SKILL.md`** as normative for generated and hand-written TypeQL

## Depends on
- #0.1 (dev stack) — same TypeDB version as local

## References
- `skills/typedb/SKILL.md`
""",
    ),
    (
        "[RPA plugin] 0.3 — Monorepo skeleton for code/rpa_plugin_skill",
        """## Milestone
M0 Foundations

## Summary
Create **`code/rpa_plugin_skill`** package layout: entrypoint process, env example (**no secrets**), scripts for `dev` / `test`, lint/format baseline.

## Acceptance criteria
- [ ] Placeholder service starts and reads **single TypeDB instance** config (URL)
- [ ] Can open **named** databases (bootstrap stub for Layer C / B / test Layer A)
- [ ] `.env.example` lists `TYPEDB_ADDRESS` (and related) without real credentials

## Depends on
- Local dev stack (**0.1**)

## References
- `a_seed/os-agent-guard-rails-overview.md` — Stage 2 path `code/rpa_plugin_skill`
""",
    ),
    (
        "[RPA plugin] 1.1 — TypeDB connection configuration (single instance)",
        """## Milestone
M1 Data planes

## Summary
Configuration for **one** TypeDB server: address, credentials (if any), timeouts; validate on startup.

## Acceptance criteria
- [ ] Single connection target in config (no multi-host requirement for v1)
- [ ] Health probe usable by UI and workers
- [ ] Document default address matching dev compose (e.g. `localhost:1729`)

## References
- `plan/rpa_guidelines_plan/PLAN.md` §4
""",
    ),
    (
        "[RPA plugin] 1.2 — Logical databases: Layer C, Layer B, Layer A per registration",
        """## Milestone
M1 Data planes

## Summary
**Naming and lifecycle** on the **single TypeDB instance**: create/list/archive **one database for Layer C**, **one for Layer B**, and **one Layer A database per** registered SQL or API source. Document mapping: registration id → Layer A DB name.

## Acceptance criteria
- [ ] Registering a new source creates a **new** Layer A database on the **same** instance
- [ ] Layer C and B databases created once (bootstrap)
- [ ] Document limits (max DBs, naming collisions, charset rules)
- [ ] All schema operations use TypeQL per **`skills/typedb/SKILL.md`**

## References
- `plan/rpa_guidelines_plan/PLAN.md` §1 (UI state + shadow)
""",
    ),
    (
        "[RPA plugin] 2.1 — Layer C schema: connections, rules, tasks, settings",
        """## Milestone
M1 Data planes

## Summary
TypeQL **`define`** for **Layer C** database: registered sources (name, URL, type `sql`|`api`), credential references (vault pointers, not plaintext), rule metadata + AST refs, task entities, **schedule metadata** for OpenClaw (cron expression, external job ref), agent profile fields (Settings).

## Acceptance criteria
- [ ] Schema committed with **`schema`** transactions per SKILL
- [ ] Migration / versioning approach documented
- [ ] Supports CRUD implied by PLAN §5.2, §5.4, §5.7

## Depends on
- **1.2**

## References
- `plan/rpa_guidelines_plan/PLAN.md` §1
""",
    ),
    (
        "[RPA plugin] 2.2 — Layer C API layer (plugin internal)",
        """## Milestone
M1 Data planes

## Summary
Typed data-access layer for UI and workers reading/writing **Layer C** only.

## Acceptance criteria
- [ ] Unit tests against test TypeDB (named Layer C DB)
- [ ] No plaintext secrets stored in attributes

## Depends on
- **2.1**
""",
    ),
    (
        "[RPA plugin] 3.1 — Layer B schema subset (17-promise-graphs.md)",
        """## Milestone
M1 Data planes

## Summary
Implement minimal **Layer B** schema in its **named database**: entities/relations per `plan/rpa_guidelines_plan/PLAN.md` §3 (`promise`, `assessment`, `action`, `session`, `task-promise`, `data-trace`, …).

## Acceptance criteria
- [ ] `define` loads in clean Layer B DB; TypeQL per **`skills/typedb/SKILL.md`**
- [ ] Mapping table: OpenClaw agent ↔ `agent`; guard check ↔ `action` + **`data-trace`**

## Depends on
- **1.2**

## References
- https://github.com/Volland/typedb-for-edge-ai-agents/blob/main/manuscript/17-promise-graphs.md
""",
    ),
    (
        "[RPA plugin] 3.2 — Seed queries + regression tests for Layer B",
        """## Milestone
M1 Data planes

## Summary
Representative insert/query scripts for promise chain, assessment, task linkage; run in CI.

## Acceptance criteria
- [ ] Automated tests pass in CI (**0.2**)

## Depends on
- **3.1**
""",
    ),
    (
        "[RPA plugin] 4.1 — Postgres DDL ingestion",
        """## Milestone
M2 Registration (SQL path)

## Summary
Fetch or accept DDL; parse to internal model for SQL registration.

## Acceptance criteria
- [ ] Supported DDL subset documented
- [ ] Clear errors for unsupported constructs

## Depends on
- **1.2**, **2.1**
""",
    ),
    (
        "[RPA plugin] 4.2 — SQL → TypeQL define + stable @key (per-app Layer A DB)",
        """## Milestone
M2 Registration (SQL path)

## Summary
Generate **that registration’s** Layer A schema: **`define`**, **`@key`**, entity/relation/attribute per **`skills/typedb/SKILL.md`**; use **`redefine`** when amending.

## Acceptance criteria
- [ ] Golden-file tests for sample schema excerpt
- [ ] CI TypeQL validation (**0.2**)
- [ ] Schema txn targets correct **named** Layer A database

## Depends on
- **4.1**

## References
- `skills/typedb/SKILL.md` — `@key`, roots
""",
    ),
    (
        "[RPA plugin] 4.3 — Register UI: SQL URL + display name + switcher",
        """## Milestone
M2 Registration (SQL path)

## Summary
PLAN §5.1: user provides **name** + **SQL connection** / DDL source; schema preview; **multiple** registrations; **switch** active context.

## Acceptance criteria
- [ ] Each registration maps to **its own Layer A** DB on the single instance
- [ ] Manual or E2E script step documented

## Depends on
- **2.2**, **4.2**
""",
    ),
    (
        "[RPA plugin] 5.1 — OpenAPI fetch + parse",
        """## Milestone
M2 Registration (API path)

## Summary
Resolve **Swagger/OpenAPI** URL to a parsed document.

## Acceptance criteria
- [ ] Document auth modes for protected specs (bearer, basic, manual paste)

## Depends on
- **1.2**, **2.1**
""",
    ),
    (
        "[RPA plugin] 5.2 — OpenAPI → TypeQL domain + extract bundles",
        """## Milestone
M2 Registration (API path)

## Summary
Components → entities/attributes; paths → extract bundles; TypeQL **`define`** into **per-app** Layer A DB.

## Acceptance criteria
- [ ] Golden tests from financial OpenAPI fragment
- [ ] JSONPath / parameter mapping documented (PLAN §6 unit testing bullet)

## Depends on
- **5.1**

## References
- `plan/financial_planner_api_scenario/` OpenAPI plans
""",
    ),
    (
        "[RPA plugin] 5.3 — Register UI: OpenAPI path",
        """## Milestone
M2 Registration (API path)

## Summary
Same as SQL path: **new Layer A DB per** API registration; OpenAPI-specific preview.

## Acceptance criteria
- [ ] Aligns with scenario SCENARIO docs for financial path

## Depends on
- **5.2**, **2.2**
""",
    ),
    (
        "[RPA plugin] 6.1 — Rule list CRUD (Layer C + Layer A link)",
        """## Milestone
M3 Rules

## Summary
PLAN §5.2: list/add/edit/delete rules per registered source; metadata in **Layer C**; rule logic in Layer A schema.

## Acceptance criteria
- [ ] Delete/update semantics consistent (tombstone vs schema removal) documented

## Depends on
- **2.2**, **4.2** or **5.2**
""",
    ),
    (
        "[RPA plugin] 6.2 — Rules composer UI: NL left; Logic + TypeQL tabs right",
        """## Milestone
M3 Rules

## Summary
PLAN §5.3: **Logic viewer** (Horn IF/THEN/ELSE + diagram); **TypeQL viewer** (read-only or propose diff).

## Acceptance criteria
- [ ] UX matches overview Basic Flow
- [ ] TypeQL tab reflects **`fun`** style per SKILL

## Depends on
- **6.1**
""",
    ),
    (
        "[RPA plugin] 6.3 — NL → Horn AST → TypeQL fun codegen",
        """## Milestone
M3 Rules

## Summary
Persist AST in Layer C; append **`fun`** via **`schema`** txn + **`redefine`**; **semicolon-terminated** fragments; validate before commit.

## Acceptance criteria
- [ ] Unit tests from AST fixtures
- [ ] Invalid rules blocked with actionable errors

## Depends on
- **6.2**

## References
- `skills/typedb/SKILL.md` — `with`, functions, semicolons
""",
    ),
    (
        "[RPA plugin] 6.4 — Hot-reload Guard MCP tool surface after rule/schema changes",
        """## Milestone
M3 Rules + MCP

## Summary
When Layer A **`fun`** / schema updates, **refresh MCP tool registry in process** — **no MCP host process restart**. Document concurrency for in-flight calls.

## Acceptance criteria
- [ ] Integration test: add rule → new tool appears **without** process restart
- [ ] Thread-safety / in-flight behavior documented

## Depends on
- **6.3**, **8.2** (ordering: may need stub 8.1 first)

## References
- Global decision: hot-load MCP
""",
    ),
    (
        "[RPA plugin] 7.1 — Sync worker: SQL → TypeQL inserts (Layer A)",
        """## Milestone
M3 Sync

## Summary
Execute generated SQL; map rows to TypeQL **`insert`/`put`** in **`write`** transactions against the **correct** Layer A DB.

## Acceptance criteria
- [ ] Idempotency or watermark strategy documented
- [ ] Integration test: Postgres + TypeDB (named Layer A)

## Depends on
- **4.2**, **6.3** (optional ordering)

## References
- `skills/typedb/SKILL.md` — `write` txn
""",
    ),
    (
        "[RPA plugin] 7.2 — Sync worker: REST → TypeQL inserts (Layer A)",
        """## Milestone
M3 Sync

## Summary
Execute REST calls per extract bundle; map to shadow entities in **that app’s** Layer A DB.

## Acceptance criteria
- [ ] Pagination / rate limits documented

## Depends on
- **5.2**
""",
    ),
    (
        "[RPA plugin] 7.3 — Sync triggers (manual + post-define hooks)",
        """## Milestone
M3 Sync

## Summary
Trigger sync after registration, after task finalize, manual **refresh**; surface status in UI.

## Acceptance criteria
- [ ] Last sync time / error visible

## Depends on
- **7.1**, **7.2**, task pipeline (**10.3**)
""",
    ),
    (
        "[RPA plugin] 8.1 — MCP server scaffold + namespaces (Guard vs Promise)",
        """## Milestone
M4 MCP

## Summary
One **long-lived** process exposing two logical **tool groups**: **Guard (Layer A)** and **Promise Graph (Layer B)**; designed for **hot reload** of Guard tools.

## Acceptance criteria
- [ ] OpenClaw (or MCP client) can list both namespaces

## Depends on
- **0.3**, **1.1**
""",
    ),
    (
        "[RPA plugin] 8.2 — Guard MCP: one tool per fun + introspection (hot registry)",
        """## Milestone
M4 MCP

## Summary
Dynamic tools invoke TypeQL against **active registration’s Layer A**; registry updates when **`fun`** set changes (**6.4**). Include **`data-trace`** inputs: rule id, schema hash, sync watermark.

## Acceptance criteria
- [ ] Contract tests: tool list matches **`fun`** set after reload
- [ ] Read/write usage per **`skills/typedb/SKILL.md`**

## Depends on
- **6.3**, **8.1**
""",
    ),
    (
        "[RPA plugin] 9.1 — Promise Graph MCP: declare / chain / assess / query (Layer B)",
        """## Milestone
M4 MCP

## Summary
Static **tool surface**, dynamic data — all against **Layer B** named database per PLAN §1 item 2.

## Acceptance criteria
- [ ] MCP contract tests; TypeQL per SKILL

## Depends on
- **3.1**, **8.1**

## References
- `17-promise-graphs.md`
""",
    ),
    (
        "[RPA plugin] 9.2 — Correlate guard action + Layer B assessment (appeals)",
        """## Milestone
M4 MCP

## Summary
Deny path records **assessment** + appeal path (PLAN §5.6 state diagram); correlation IDs across C/B/A.

## Acceptance criteria
- [ ] Trace from dashboard row to assessments + optional Layer A refs

## Depends on
- **8.2**, **9.1**
""",
    ),
    (
        "[RPA plugin] 10.1 — Task list CRUD (Layer C)",
        """## Milestone
M5 Tasks

## Summary
PLAN §5.4: tasks scoped to active registration.

## Acceptance criteria
- [ ] CRUD in Layer C schema

## Depends on
- **2.2**
""",
    ),
    (
        "[RPA plugin] 10.2 — Task composer UI: description + schema-aware flow chart",
        """## Milestone
M5 Tasks

## Summary
PLAN §5.5: left **description**, right **flow chart**; highlight object names / process logic using **that registration’s Layer A** schema.

## Acceptance criteria
- [ ] Manual test step in SCENARIO docs

## Depends on
- **10.1**, **4.2** or **5.2**
""",
    ),
    (
        "[RPA plugin] 10.3 — Task description → SQL/API plan + Layer A load",
        """## Milestone
M5 Tasks

## Summary
Background: convert description to queries; **`write`** txn to Layer A; **ready to schedule** + preview.

## Acceptance criteria
- [ ] “Task ready to schedule” state; preview counts/rows

## Depends on
- **10.2**, **7.1**, **7.2**
""",
    ),
    (
        "[RPA plugin] 11.1 — Schedules via OpenClaw cron / OpenClaw executor (no standalone OS cron)",
        """## Milestone
M5 Runs

## Summary
Persist schedule intent in **Layer C** (cron expression, labels, task id). **Execution** delegated to **OpenClaw’s cron service** or **another OpenClaw skill** calling the plugin’s **documented run endpoint** (MCP tool and/or HTTP). Plugin does **not** ship its own OS-level scheduler.

## Acceptance criteria
- [ ] Example OpenClaw cron / skill config in repo
- [ ] Document contract: payload, auth, idempotency, target registration / Layer A DB

## Depends on
- **10.3**, **2.1**
""",
    ),
    (
        "[RPA plugin] 11.2 — Run orchestrator: Sync → Precheck (Guard) → Act → Review",
        """## Milestone
M5 Runs

## Summary
Implement PLAN §5.6 state machine; single **run task** entrypoint suitable for **OpenClaw-invoked** execution.

## Acceptance criteria
- [ ] Deny path: assessment + appeal
- [ ] Act path: RPA steps + Promise MCP logging

## Depends on
- **11.1**, **8.2**, **9.1**, **7.3**
""",
    ),
    (
        "[RPA plugin] 11.3 — Task Inspector dashboard (runs, promises, overrides, appeals)",
        """## Milestone
M5 Review

## Summary
PLAN §5.7: runs, promises, assessments, decision variables, **override**, **appeal**.

## Acceptance criteria
- [ ] Full trace across Layer C / B / correct Layer A

## Depends on
- **9.2**, **11.2**
""",
    ),
    (
        "[RPA plugin] 12.1 — Settings: TypeDB URL, DB names, OpenClaw integration hooks",
        """## Milestone
M5 Ops

## Summary
PLAN Settings: **one instance** URL; defaults for **Layer C** / **Layer B** DB names; agent identity; **OpenClaw**-related settings (cron profile, webhook path, token for triggered runs).

## Acceptance criteria
- [ ] Validate connection on save; secrets not in repo

## Depends on
- **2.2**, **11.1**
""",
    ),
    (
        "[RPA plugin] 13.1 — OpenClaw skill package: manifest, config, prompts",
        """## Milestone
M6 Agent integration

## Summary
Installable skill under **`code/rpa_plugin_skill`**; documents **single TypeDB instance** + **named DBs**.

## Acceptance criteria
- [ ] Example OpenClaw config snippet in repo

## Depends on
- **8.2**, **9.1**
""",
    ),
    (
        "[RPA plugin] 13.2 — Always precheck + OpenClaw cron / companion skill wiring",
        """## Milestone
M6 Agent integration

## Summary
Agent workflow + **scheduled runs** via OpenClaw (**11.1** cross-link).

## Acceptance criteria
- [ ] End-to-end doc: cron/skill → run endpoint → Guard + Promise MCP

## Depends on
- **13.1**, **11.2**
""",
    ),
    (
        "[RPA plugin] 14.1 — A/B mode: run tasks with vs without guard rails",
        """## Milestone
M6 Comparison

## Summary
Overview §11 / PLAN: flag to compare runs; labeled in inspector.

## Acceptance criteria
- [ ] Same task runnable in A/B with clear labels in dashboard
- [ ] DEMO.md scripts can reference mode toggle

## Depends on
- **11.2**, **13.2**
""",
    ),
    (
        "[RPA plugin] 15.1 — Integration: Docker Compose full stack (TypeDB + optional SoR)",
        """## Milestone
M7 Quality

## Summary
Compose: **one TypeDB**, optional Postgres/API for integration tests; plugin; **simulate OpenClaw** trigger via documented HTTP/MCP call.

## Acceptance criteria
- [ ] One-command smoke documented

## Depends on
- **7.1**, **7.2**, **8.2**, **9.1**
""",
    ),
    (
        "[RPA plugin] 15.2 — E2E harness vs SCENARIO.md (medical + financial)",
        """## Milestone
M7 Quality

## Summary
Automate where feasible; otherwise checklist runner for `plan/*/SCENARIO.md`.

## Acceptance criteria
- [ ] Traceability: scenario step ↔ test

## Depends on
- **15.1**
""",
    ),
    (
        "[RPA plugin] 15.3 — Security hardening (credentials, triggered-run auth, audit)",
        """## Milestone
M7 Quality

## Summary
Least privilege on SoR credentials; auth for OpenClaw-triggered runs; audit trail for overrides/appeals.

## Acceptance criteria
- [ ] Short threat-model note in `plan/` or `docs/`

## Depends on
- **12.1**
""",
    ),
    (
        "[RPA plugin] 15.4 — Root README: links + TypeQL skill reference",
        """## Milestone
M7 Docs

## Summary
Ensure root `README.md` links RPA plugin plan, scenarios, demos; point to **`skills/typedb/SKILL.md`**.

## Acceptance criteria
- [ ] Matches overview deliverable for discoverability

## Depends on
— (can run anytime)
""",
    ),
]


def main() -> None:
    if len(ISSUES) != 40:
        print(f"Expected 40 issues, got {len(ISSUES)}", file=sys.stderr)
        sys.exit(1)
    for title, body in ISSUES:
        create_issue(title, body)
    print("Done. Created", len(ISSUES), "issues.")


if __name__ == "__main__":
    main()
