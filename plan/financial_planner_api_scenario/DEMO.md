# Financial planner API scenario — Investor demo scripts

**Audience:** Local WSL + Docker; **Swagger UI** + MongoDB; synthetic clients only.  
**Disclaimer:** Fictional portfolios; not investment advice.

This document maps **which rules (FP-Rxx)** and **which tasks (F1–F5)** from [`SCENARIO.md`](SCENARIO.md) are required for each demo length. Prep seed data: **`C-ALLOW`**, **`C-DENY`**, **`C-NON-ACC`** as referenced in the scenario.

---

## Rules and tasks — quick reference

| ID | Included in |
|----|-------------|
| **Rules** | |
| FP-R01, FP-R02 | 1 min, 5 min, 20 min |
| FP-R06 | 5 min, 20 min |
| FP-R03, FP-R04, FP-R05, FP-R07, FP-R08, FP-R09, FP-R10, FP-R11, FP-R12 | 20 min only (full set); subset named per block below |
| **Tasks** | |
| F2 (DENY concentration) | 1 min, 5 min, 20 min |
| F1 (ALLOW recommendation) | 5 min, 20 min |
| F3 (trade preview/execute) | 20 min |
| F4 (KYC DENY) | 20 min |
| F5 (trace_id) | 20 min |

---

## 1-minute demo

**Goal:** One life-safety–style financial guard in one breath (concentration).

| Element | Use |
|---------|-----|
| **Rules** | **FP-R01** only (optionally mention **FP-R12** if you show sector). |
| **Tasks** | **F2** only — client **`C-DENY`**, `POST /recommendations` (or equivalent) blocked for concentration. |

**Script:** Show **`C-DENY`** holdings in Swagger or mini-app → run **F2** → **Guard MCP DENY** + witness (symbol, %) → **Promise** line item → closing: policy in **`fun`**, not the prompt.

---

## 5-minute demo

**Goal:** OpenAPI shadow + two-rule story + task-driven extract + ALLOW + DENY.

| Element | Use |
|---------|-----|
| **Rules** | **FP-R01**, **FP-R02**, **FP-R06** (idempotency visible on headers). |
| **Tasks** | **F1** (`C-ALLOW`) then **F2** (`C-DENY`). |

| Min | Step |
|-----|------|
| 0:00 | One-liner: API-first shadow + MongoDB + guard + promises. |
| 0:45 | **Register** OpenAPI + show **Swagger UI** full docs. |
| 1:30 | **Rules:** show **FP-R01** + **FP-R02** in composer (Logic + TypeQL tabs). |
| 2:15 | **Task F1:** show **extract** definition (GETs listed in **SCENARIO**); **run** → data imported → **ALLOW**. |
| 3:30 | **Task F2:** same extract pattern for **`C-DENY`** → **DENY** + witness. |
| 4:30 | **Promise** dashboard snippet. |
| 4:50 | Close: dual MCP + audit. |

**Not in scope for 5 min:** FP-R03–R05, R07–R12, tasks F3–F5.

---

## 20-minute demo

**Goal:** Full rule set, task portfolio, and governance story.

| Element | Use |
|---------|-----|
| **Rules** | **FP-R01** through **FP-R12** (all). |
| **Tasks** | **F1**, **F2**, **F3**, **F4**, **F5** (order can be narrative-driven). |

| Block | Content |
|-------|---------|
| **0–3 min** | Problem: stateless agents + raw APIs; need **typed** policy + audit. |
| **3–7 min** | Architecture: OpenAPI → Layer A; [`17-promise-graphs.md`](https://github.com/Volland/typedb-for-edge-ai-agents/blob/main/manuscript/17-promise-graphs.md) Layer B; dual MCP. |
| **7–11 min** | **Swagger** walkthrough: clients, accounts, holdings, recommendations, trades. |
| **11–14 min** | **Rules list** — scroll **FP-R01**–**FP-R12**; pick **FP-R04** + **FP-R05** to explain disclosure + preview ordering. |
| **14–17 min** | **Tasks:** **F1** ALLOW, **F2** DENY, **F3** trade path, **F4** KYC DENY, **F5** **`trace_id`**. |
| **17–19 min** | **Dashboard** + override. |
| **19–20 min** | Roadmap: `code/financial_planner_api_scenario`, CI. |

---

## Backup

- Pre-recorded **curl** + Problem Details JSON for **F5**; static architecture slide if TypeDB is down.
