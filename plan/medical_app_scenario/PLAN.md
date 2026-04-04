# Medical mini-app — Build plan (`plan/medical_app_scenario`)

**Purpose:** Dummy **Postgres + web UI** for Scenario 1 (SQL → TypeQL shadow path). **Stage 1** documentation; **Stage 2** implementation lives in `code/medical_app_scenario` (per overview).

**Richness target:** [Complete Medical Trial Example](https://github.com/Volland/typedb-for-edge-ai-agents/blob/main/manuscript/13-hypergraphs.md#complete-medical-trial-example) — **`trial-enrollment`** as n-ary hyperedge (patient, trial, **multiple** prescribers, **multiple** medications, site), **`adverse-event`**, optional **`trial-enrollment-review`** (relation-on-relation), contraindications, allergies, outpatient **prescriptions**.

**Environment:** **WSL 2** + **Docker Desktop** on Windows; all services bind **localhost** for OpenClaw iframe embedding.

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
- **One command:** `docker compose up -d` from WSL.

---

## 6. Seed generation

- **Python** or **SQL** script: deterministic demo data set for reproducible investor demos.  
- **Edge cases baked in:** allergy conflict, trial concomitant violation, pediatric + warning drug, AE Query-4 pattern (prescriber = reporter), duplicate therapy, unverified allergy only.

---

## 7. Testing (mini-app)

- `psql` assertions: FKs, row counts, specific fixture IDs.  
- API smoke: CRUD on enrollment creates correct junction rows.  
- Optional: Playwright — open patient, submit prescription form.

---

## 8. TypeQL shadow (Layer A) — plugin concern

Transpile DDL → PERA-style **`trial-enrollment`** relation with roles; sync from SQL extracts. **`fun`** catalog in **SCENARIO.md**.

---

## 9. Disclaimer

Synthetic PHI; **not** for clinical production.
