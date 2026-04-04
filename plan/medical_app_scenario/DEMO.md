# Medical scenario — Investor demo scripts

**Audience:** Investor on a **local machine** (WSL + Docker): real browser, real TypeDB, synthetic data only.  
**Disclaimer (say aloud):** Fictional clinical data; not a regulated medical device.

Maps **which rules (MED-Rxx)** and **which tasks (M1–M6)** from [`SCENARIO.md`](SCENARIO.md) to each demo length. Prep seeds: **`P-ALLOW`**, **`P-ALLERGY`**, **`P-TRIAL`**, **`P-AE`**, plus enrollment/review fixtures per **PLAN.md**.

---

## Rules and tasks — quick reference

| ID | Included in |
|----|-------------|
| **Rules** | |
| MED-R01 | 1 min, 5 min, 20 min |
| MED-R02, MED-R03, MED-R04, MED-R06, MED-R07, MED-R08, MED-R09, MED-R10, MED-R11, MED-R12 | 20 min (full set); subsets named per section |
| **Tasks** | |
| M2 (allergy DENY) | 1 min, 5 min, 20 min |
| M1 (ALLOW rx) | 5 min, 20 min |
| M3 (trial concomitant) | 20 min |
| M4 (open AE block) | 20 min |
| M5 (enrollment review gate) | 20 min |
| M6 (AE reporter consistency) | 20 min |

---

## 1-minute demo

**Goal:** One life-safety guard in one breath.

| Element | Use |
|---------|-----|
| **Rules** | **MED-R01** only. |
| **Tasks** | **M2** only — patient **`P-ALLERGY`**, prescribe conflicting medication. |

**Script:** Show allergy row in UI → run **M2** → **Guard MCP DENY** + rule name → **Promise** line → closing: shadow graph + MCP blocked unsafe action.

---

## 5-minute demo

**Goal:** Postgres → TypeQL schema + two-rule path + **task-defined extract** + ALLOW + DENY.

| Element | Use |
|---------|-----|
| **Rules** | **MED-R01**, **MED-R02** (contraindication can be mentioned in Logic viewer). |
| **Tasks** | **M1** (`P-ALLOW`) then **M2** (`P-ALLERGY`). |

| Min | Step |
|-----|------|
| 0:00 | One-liner: typed guard rails + promise audit for clinical RPA. |
| 0:40 | **Register** Postgres → **TypeQL** schema (trial-enrollment pattern). |
| 1:20 | **Rules:** composer for **MED-R01** (+ optional **MED-R02** snippet). |
| 2:00 | **Task M1:** show **extract** (tables: patient, allergies, meds, ingredients); **run** → import → **ALLOW**. |
| 3:15 | **Task M2:** same extract pattern for **`P-ALLERGY`** → **DENY** + witness. |
| 4:15 | Optional: **trial enrollment** UI with two prescribers + two meds (data story only, no extra tasks). |
| 4:45 | **Promise** graph: session + task + assessment. |

**Not in scope for 5 min:** MED-R03–R12, tasks M3–M6.

---

## 20-minute demo

**Goal:** Full hypergraph story + rule breadth + task portfolio.

| Element | Use |
|---------|-----|
| **Rules** | **MED-R01** through **MED-R12** (all). |
| **Tasks** | **M1**–**M6** (order below is suggested narrative). |

| Block | Content |
|-------|---------|
| **0–3 min** | Problem: agents + raw EHR/SQL aren’t enough; need **queryable** policy + audit (`agent_book`). |
| **3–7 min** | **Layer A** + **`fun`**; **Layer B** [promise graphs](https://github.com/Volland/typedb-for-edge-ai-agents/blob/main/manuscript/17-promise-graphs.md); dual MCP. |
| **7–11 min** | **Medical app:** patients, trials, **enrollment** + junctions, AE, **enrollment review** metagraph. |
| **11–15 min** | **Rules** scroll **MED-R01**–**MED-R12**; deep-dive **MED-R07** + **MED-R08** (hypergraph). |
| **15–18 min** | **Tasks:** **M1** ALLOW, **M2** DENY, **M3** trial, **M4** AE block, **M5** review gate, **M6** reporter consistency. |
| **18–19 min** | **Dashboard** + appeal/override. |
| **19–20 min** | Roadmap: `code/medical_app_scenario`, `code/rpa_plugin_skill`. |

**Optional A/B (overview §11):** ≤2 min, dev-only, **with** vs **without** guard hooks.

---

## Backup plan

- Pre-recorded MCP JSON + dashboard; live **medical UI** + static architecture slide if TypeDB unavailable.
