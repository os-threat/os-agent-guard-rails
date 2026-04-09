# Medical mini-app — Build plan (`plan/medical_app_scenario`)

**Purpose:** Dummy **Postgres + web UI** for Scenario 1 (SQL → TypeQL shadow path). **Stage 1** documentation; **Stage 2** implementation lives in `code/medical_app_scenario` (per overview).

**Richness target:** [Complete Medical Trial Example](https://github.com/Volland/typedb-for-edge-ai-agents/blob/main/manuscript/13-hypergraphs.md#complete-medical-trial-example) — **`trial-enrollment`** as n-ary hyperedge (patient, trial, **multiple** prescribers, **multiple** medications, site), **`adverse-event`**, optional **`trial-enrollment-review`** (relation-on-relation), contraindications, allergies, outpatient **prescriptions**.

**Development:** Code and develop the mini-app in this repo on **Windows** (Cursor, git, Node/Python as needed). **Runtime:** **Docker Desktop** (and optionally **WSL 2** for compose shells); all services bind **localhost** for OpenClaw iframe embedding.

---

## 1. Repository layout (Stage 2 target)

```
code/medical_app_scenario/          # implementation (future)
  docker-compose.yml
  db/
    schema.sql
    migrations/                     # optional
  seed/
    generate_data.py                # or generate_data.sql — target hundreds of rows
    data.sql                        # generated import
  web/
    public/
    src/                            # views + forms (see §4)
  tests/
    test_db.sh
    test_ui.spec.ts                 # optional Playwright
plan/medical_app_scenario/
  PLAN.md                           # this file
  SCENARIO.md
  DEMO.md
```

---

## 2. Data volume (overview: “few hundred rows”)

| Area | Approx. rows | Notes |
|------|----------------|-------|
| `patients` | ~80–120 | Mix pediatrics/adults for age rules |
| `doctors` / `clinicians` | ~25–40 | physician vs pharmacist vs investigator |
| `hospitals` / `sites` | ~10–15 | |
| `medications` | ~60–100 | ingredient linkage for allergies |
| `medication_ingredients` | ~100+ | many-to-many med ↔ ingredient |
| `patient_allergies` | ~150–250 | verified vs unverified |
| `medication_contraindications` | ~40–80 | condition / age rules |
| `trials` | ~5–8 | |
| `trial_enrollments` | ~40–80 | header rows |
| `trial_enrollment_prescribers` | ~60+ | multi-prescriber enrollments |
| `trial_enrollment_medications` | ~80+ | multi-drug enrollments |
| `adverse_events` | ~30–60 | link some to enrollment |
| `trial_enrollment_reviews` | ~20–40 | pending/approved |
| `prescriptions` (non-trial) | ~200–400 | main volume driver |

**Total:** **roughly 300–800+** rows across tables — tune generator so **≥400** inserted lines in `data.sql` is acceptable for demos.

### 2.1 Demo fixture patients (synthetic names, multiple per condition)

Seeds must use **realistic first + last names** (not codes like `P-ALLOW`). Each **demo condition** below needs **at least three** distinct patients so investors see repeatability, not a one-off row.

| Demo focus | Role | Example patients (≥3 each in seed) |
|------------|------|--------------------------------------|
| **M1** — outpatient **ALLOW** | No allergy clash, no blocking open severe AE | Jordan Hayes, Morgan Reed, Taylor Brooks |
| **M2** — **DENY** (verified allergy vs proposed med ingredients) | Verified β-lactam / penicillin-class conflict exemplars | Riley Chen, Alex Rivera, Casey Nguyen |
| **M3** — trial **concomitant / allowed-list** DENY | Enrolled; proposed med off trial allowed list | Sam Okonkwo, Jamie Foster, Drew Patel |
| **M4** — open **severe AE** blocks new rx | Open severity ≥ policy threshold (e.g. G3+) | Avery Morrison, Blake Okada, Dakota Flynn |
| **M5** — **enrollment review** not approved | Trial-related action while review pending | Nico Harper, Remy Santos, Sage Lombardi |
| **M6** — **AE reporter** not on enrollment prescriber junction | AE linked to enrollment; reporter ∉ `trial_enrollment_prescribers` | Lake Kim, Rowan Gupta, Skyler Adams |

Overlap is fine (e.g. a patient can appear in both M3 and M5 narratives) as long as **every** row remains **synthetic** and the **≥3 exemplars per scenario** rule is satisfied. Document primary vs alternate picks for each task in [`SCENARIO.md`](SCENARIO.md) / [`DEMO.md`](DEMO.md).

---

## 3. Postgres schema (relational mirror of hypergraph)

### 3.1 Core (book-aligned)

- `patients` — PK, `patient_id` business key, name, dob, optional `age` computed in UI.
- `trials` — `trial_id`, title, dates, phase, status.
- `doctors` — `license_id` UNIQUE, name, `role` (physician/pharmacist/investigator), specialty.
- `hospitals` — `hospital_id`, name, address.
- `medications` — `drug_code` UNIQUE, name, optional `warning` text (minors, pregnancy).
- `ingredients`, `medication_ingredients` — allergy matching.
- `adverse_event_types` — code + description.

### 3.2 `trial_enrollments` + junctions

- `trial_enrollments` — PK, `patient_id`, `trial_id`, `site_id` NULLABLE, `enrolled_at`, `status`.
- `trial_enrollment_prescribers` — (`enrollment_id`, `doctor_license`) PK.
- `trial_enrollment_medications` — (`enrollment_id`, `drug_code`) PK.

### 3.3 `adverse_events`

- FK `patient_id`, `event_type_code`, `reporting_physician_license`, optional `enrollment_id`, `severity`, `reported_at`.

### 3.4 Metagraph (book)

- `trial_enrollment_reviews` — `enrollment_id`, `reviewer_license`, `approval_status`, `reviewed_at`.

### 3.5 Clinical extensions (overview)

- `patient_conditions`, `patient_allergies` (ingredient or drug), `medication_contraindications`.
- `prescriptions` — outpatient path: patient, prescriber, medication, site, dose, frequency, dates, status.

### 3.6 Views for UI

- `v_patient_timeline` — union of prescriptions, AEs, enrollments (for demo lists).
- `v_enrollment_detail` — enrollment + aggregated prescriber/med lists.

---

## 4. Web UI (iframe-friendly, “all views and forms”)

**Stack (suggested):** Node + Express or Vite + React; **read/write** against Postgres via API layer (never expose DB port to browser in prod demo; localhost OK).

**Screens**

1. **Dashboard** — counts: active trials, open AEs, pending reviews.  
2. **Patients** — searchable table → **detail**: allergies, conditions, enrollments, prescriptions, AEs.  
3. **Trials** — list → detail + enrollments list.  
4. **Enrollment form** — pick patient, trial, site; **multi-select** prescribers and medications (validates junction model).  
5. **Prescription form** — standard outpatient rx (RPA target).  
6. **Adverse event form** — link optional enrollment.  
7. **Enrollment review** — approve/reject (workflow for guard demos).  
8. **Admin** — re-seed button **dev only**.

**Ports (example):** Web `8081`, Postgres `5433` — document in `README`.

---

## 5. Docker

- **Services:** `postgres:16` (or 15), optional `pgadmin`.  
- **Volumes:** persist DB for iterative demos.  
- **Healthcheck:** `pg_isready`.  
- **One command:** `docker compose up -d` from the repo (PowerShell, cmd, or WSL path to the same directory).

---

## 6. Seed generation

- **Python** or **SQL** script: deterministic demo data set for reproducible investor demos.  
- **Edge cases baked in:** allergy conflict, trial concomitant violation, pediatric + warning drug, AE pattern where reporter aligns with enrollment prescriber (clean case) **and** mismatch cases for **M6**, duplicate therapy, unverified allergy only.  
- **Fixture depth:** For **each** row in §2.1, include **at least three** patients in that category (distinct names/rows), not a single exemplar. Include mixed ages/sites and a few **negative controls** (patients who do **not** trigger a given guard) where useful for UI search demos.

---

## 7. Testing (mini-app)

- `psql` assertions: FKs, row counts, **≥3 seed rows per §2.1 category**, and spot checks by **patient name** / business key (e.g. Riley Chen present with expected allergy edges).  
- API smoke: CRUD on enrollment creates correct junction rows.  
- Optional: Playwright — open patient, submit prescription form.

---

## 8. TypeQL shadow (Layer A) — plugin concern

Transpile DDL → PERA-style **`trial-enrollment`** relation with roles; sync from SQL extracts. **`fun`** catalog in **SCENARIO.md**.

---

## 9. Disclaimer

Synthetic PHI; **not** for clinical production.
