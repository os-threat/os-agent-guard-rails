# Medical scenario — Using OS-Agent RPA Guard Rails (end-user story)

**Companion:** [`PLAN.md`](PLAN.md) (mini-app build), [`DEMO.md`](DEMO.md) (investor timing).  
**Prereqs:** Mini-app running (**WSL + Docker**), plugin **Stage 2**, TypeDB for shadow + promise graph.

This document is the **manual script** for overview **Deliverables / Stage 2** §4–5. You add the **exact rules** and **exact tasks** below in the plugin UI.

**Shadow data import is driven by tasks:** each **task definition** specifies which **SQL extracts** (which tables, joins, filters, keys) populate TypeDB Layer A for that run. There is **no** separate “sync everything” step that must complete before you define tasks—unless the product adds an optional global sync, the **authoritative** extract for these demos is **per task**.

---

## 0. Actors

- **User** — configures rules and tasks (including extract scope).  
- **OpenClaw agent** — RPA against the **medical web UI** (or API).  
- **Optional reviewer** — human for appeals/overrides (mapped to `agent` in the promise graph).

---

## 1. Connect to the dummy database (schema only)

1. Start stack: `docker compose up` in `code/medical_app_scenario` (when implemented).  
2. **OS-Agent Guard Rails** → **Register** → **SQL / Postgres**.  
3. Connection string, database name, credentials (localhost port per **PLAN.md**, e.g. **5433**).  
4. **Background:** plugin reads SQL **DDL** convert to TypeQL schema→ **TypeQL `define`** for Layer A (**schema only**).  
5. Confirm types: `patient`, `trial`, `trial-enrollment` pattern, `prescription`, `adverse_event`, junctions, etc.

**Success criteria:** Registration green; **TypeQL viewer** shows schema; **no** requirement to load all rows yet.

---

## 2. Add the rule set (exact list)

Create **one rule set** (e.g. `medical-trials-v1`) and add **these twelve rules**. Use **Rule ID** in demos and dashboards.

| ID | Rule name (short) | Natural language (paste or paraphrase) | Guard MCP tool name (suggested) |
|----|-------------------|----------------------------------------|-----------------------------------|
| **MED-R01** | Verified allergy vs ingredients | If the patient has a **verified** allergy to any **ingredient** of the proposed medication, **deny** the new prescription or trial med add. | `med_allergy_ingredient_deny` |
| **MED-R02** | Contraindication vs condition | If an **absolute** contraindication exists between **patient condition** and **medication / class**, deny. | `med_contraindication_condition` |
| **MED-R03** | Trial allowed medication list | If the patient is **enrolled** in a trial, deny if the proposed medication is **not** on that trial’s **allowed** list for that enrollment. | `med_trial_allowed_medication` |
| **MED-R04** | Severe open AE blocks new rx | If the patient has an **open** adverse event with **severity** ≥ policy threshold (e.g. G3+), deny **new** prescriptions until resolved or downgraded per policy. | `med_open_severe_ae_block` |
| **MED-R05** | Duplicate same-class therapy | Deny if the proposal would create **duplicate active therapy** in the same **drug class** without explicit substitution intent. | `med_duplicate_same_class` |
| **MED-R06** | Enrollment review before trial action | For **trial-related** prescribing at a trial site, deny if the **trial enrollment review** is not **approved**. | `med_enrollment_review_approved` |
| **MED-R07** | Enrollment medication integrity | For an active enrollment, every **prescribed** trial medication must appear on **`trial_enrollment_medications`** for that enrollment. | `med_enrollment_med_junction` |
| **MED-R08** | AE reporter vs enrollment prescriber | If an AE is **linked** to an enrollment, the **reporting** prescriber must be **on** `trial_enrollment_prescribers` for that enrollment (hypergraph consistency). | `med_ae_reporter_enrollment_prescriber` |
| **MED-R09** | Pediatric + minor warning | If the patient is **under 18 years** and the medication has a **pediatric warning** flag, deny unless override path. | `med_pediatric_warning` |
| **MED-R10** | Pharmacist scope | Deny certain **trial enrollment** or **controlled** actions if the acting role is **pharmacist** where policy requires **physician/investigator**. | `med_pharmacist_scope` |
| **MED-R11** | Unverified allergy | If allergy is **unverified**, do not hard-deny for MED-R01; return **UNKNOWN** / **WARN** and route to verification workflow per policy. | `med_allergy_unverified_warn` |
| **MED-R12** | Prescriber on enrollment | For **trial-related** prescriptions, the **prescriber** must be listed on **`trial_enrollment_prescribers`** for that patient’s active enrollment. | `med_prescriber_on_enrollment` |

**Success criteria:** **MED-R01**–**MED-R12** present; **`fun`** in schema; data still optional.

---

## 3. Define RPA tasks (each task defines SQL extraction into TypeDB)

For each task: **Tasks** → **New task** — name, parameters, agent profile, browser script (or API), and **extract definition**: the **SELECTs** / views that pull `patient`, `allergy`, `medication`, `ingredient`, `enrollment` + junctions, `ae`, `review`, `prescription` rows needed for the guards in that task.

### Task M1 — “Outpatient prescription — ALLOW (safe patient)”

- **Goal:** **ALLOW** for patient **`P-ALLOW`** (seed): no allergy conflict, no blocking AE.  
- **Parameters:** `patient_mrn`, `medication_id`, prescriber license, site.  
- **Extract:** `patients` + `patient_allergies` + `patient_conditions` + `medications` + `medication_ingredients` + open `prescriptions` for interaction checks; **MED-R01, R02, R05, R11** inputs.  
- **Guard hooks:** MED-R01–R03, R05, R11 as applicable.  
- **Promise:** session + shared-task + pre/post promises.

### Task M2 — “Outpatient prescription — DENY (allergy conflict)”

- **Goal:** **DENY** for **`P-ALLERGY`** vs penicillin-class drug (seed).  
- **Extract:** same slice as M1 for that patient + proposed med ingredients.  
- **Guard hooks:** **MED-R01** (primary).  
- **Expected:** DENY + witness (ingredient ids).

### Task M3 — “Trial enrollment medication — concomitant violation”

- **Goal:** **DENY** for **`P-TRIAL`** when proposed med not on allowed list — **MED-R03**, **MED-R07**.  
- **Extract:** `trial_enrollments`, junctions `trial_enrollment_prescribers`, `trial_enrollment_medications`, `trials`, `medications`.  
- **Guard hooks:** MED-R03, R06, R07, R12.

### Task M4 — “New rx blocked by open severe AE”

- **Goal:** **MED-R04** for **`P-AE`** with open severe AE.  
- **Extract:** `adverse_events` + enrollment link + patient.  
- **Guard hooks:** MED-R04.

### Task M5 — “Enrollment review gate”

- **Goal:** **MED-R06** — trial-related action while review **pending**.  
- **Extract:** `trial_enrollment_reviews` + enrollment + patient.  
- **Guard hooks:** MED-R06 (and R08 for a second run if AE filed).

### Task M6 — “Hypergraph AE consistency (reporter vs prescribers)”

- **Goal:** **MED-R08** — AE linked to enrollment but reporter not on prescriber junction (seed failure case).  
- **Extract:** `adverse_events` + enrollment junctions.  
- **Guard hooks:** MED-R08.

---

## 4. Import shadow data (per task run)

When you **run** a task (or dry-run):

1. Plugin runs the **extract** attached to that task against Postgres.  
2. **Background:** **TypeQL insert/put** into Layer A for that scope.  
3. UI shows **timestamp**, **row counts**, **UNKNOWN** where extracts are incomplete (CWA semantics per `agent_book`).

**Important:** **M1** does not require loading the entire hospital network—only the **rows needed for M1’s guards**. **M3** pulls more enrollment-shaped data.

---

## 5. Schedule and run

1. **Schedule** or run ad hoc: **M2** for investor DENY, **M1** for ALLOW.  
2. **Live log:** MCP calls, ALLOW/DENY/UNKNOWN.  
3. **Deny:** reason + **witness** ids; promise **broken** / **blocked** with assessment.  
4. **Allow:** row in Postgres; **action** + **result** on promise graph.

---

## 6. Evaluate results and promise statistics

1. **Dashboard — Tasks:** status, ALLOW vs DENY vs UNKNOWN.  
2. **Dashboard — Promises:** fulfillment, broken, assessments (aligned with [`17-promise-graphs.md`](https://github.com/Volland/typedb-for-edge-ai-agents/blob/main/manuscript/17-promise-graphs.md)).  
3. **Guard effectiveness:** counts by **MED-Rxx**.  
4. **Appeal / override:** denied run → override with reason → **decision** + **assessment**.  
5. **A/B (overview §11):** same scripted steps **with** vs **without** guard hooks (dev-only, labeled).

---

## 7. Artifacts for investor

- Dashboard screenshot; **one DENY** trace (**M2** or **M3**); **one ALLOW** (**M1**); promise assessment line.
