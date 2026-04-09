# Creates GitHub issues for the medical mini-app (plan/medical_app_scenario).
# Prerequisite: gh auth login (https://cli.github.com/)
# Usage: pwsh scripts/create-medical-mini-app-issues.ps1
# Run from repo root. Optional labels require repo permissions; script uses none by default.

$ErrorActionPreference = "Stop"
$gh = if (Get-Command gh -ErrorAction SilentlyContinue) { "gh" } else { Join-Path $env:ProgramFiles "GitHub CLI/gh.exe" }
if (-not (Test-Path $gh) -and $gh -notmatch "^gh$") {
  Write-Error "GitHub CLI not found. Install from https://cli.github.com/ or add gh to PATH."
}

function New-GhIssue {
  param([string]$Title, [string]$Body)
  & $gh issue create --title $Title --body $Body
}

$issues = @(
  @{
    Title = "[medical] Scaffold code/medical_app_scenario with Docker Compose and README"
    Body = @'
## Goal
Create `code/medical_app_scenario/` per `plan/medical_app_scenario/PLAN.md` §1.

## Environment
- **Development:** Windows (this repo, Cursor, Node/Python).
- **Runtime:** Docker Desktop; optional WSL for a Unix shell. `docker compose` may be run from PowerShell or WSL against the same project directory.

## Decisions
- **Stack:** Pick one and document: Node + Express *or* Vite + SPA + API (suggested: Vite + React + Express API for iframe-friendly UI).
- **Ports:** Web **8081**, Postgres **5433** (PLAN §4, §5).

## Deliverables
- `docker-compose.yml`: `postgres:16` (or 15), volume, `pg_isready` healthcheck, optional pgAdmin.
- `README.md`: Docker one-liner `docker compose up -d`, connection string, synthetic PHI disclaimer.
- `.env.example` for DB URL / credentials.

## Acceptance
- From `code/medical_app_scenario`, `docker compose up -d` starts Postgres; healthcheck passes.

## Ref
- `plan/medical_app_scenario/PLAN.md` §1, §5
'@
  }
  @{
    Title = "[medical] Implement full Postgres schema (DDL) + guard-driven extensions"
    Body = @'
## Goal
Implement relational schema mirroring PLAN §3 and SCENARIO rules M1–M6 / MED-R01–R12.

## Tables (from PLAN)
Core: patients, trials, doctors, hospitals, medications, ingredients, medication_ingredients, adverse_event_types, trial_enrollments, trial_enrollment_prescribers, trial_enrollment_medications, adverse_events, trial_enrollment_reviews, patient_conditions, patient_allergies, medication_contraindications, prescriptions.

## Extensions (add explicitly)
- **MED-R03 / M3:** Trial allowed medications (e.g. `trial_allowed_medications` with `trial_id`, `drug_code`) or documented equivalent.
- **MED-R05:** Medication **drug class** (column or `drug_classes` + FK).
- **MED-R09:** Pediatric warning as boolean or enum (align with PLAN warning text).
- **MED-R10:** Controlled substance or pharmacist-restricted flag / metadata for demos.
- **patient_allergies:** `verified` (boolean) and target type (ingredient vs drug) for MED-R01 / R11.
- **adverse_events:** `severity`, `reported_at`, open/resolved as needed for MED-R04.
- **trial_enrollment_reviews:** `approval_status`, `reviewed_at`, `reviewer_license` per PLAN §3.4.

## Demo names
Fixture roster (≥3 patients per scenario) is **`plan/medical_app_scenario/PLAN.md` §2.1** — use realistic first + last names, not codes like `P-ALLOW`.

## Deliverables
- `db/schema.sql` (or migrations) loads on empty DB without errors.

## Acceptance
- `psql` loads schema; FK graph matches PLAN + extensions.

## Ref
- `plan/medical_app_scenario/PLAN.md` §3, §2.1
- `plan/medical_app_scenario/SCENARIO.md`
'@
  }
  @{
    Title = "[medical] Add v_patient_timeline and v_enrollment_detail views"
    Body = @'
## Goal
Implement PLAN §3.6 views.

## Deliverables
- `v_patient_timeline`: union of prescriptions, adverse events, enrollments for patient detail.
- `v_enrollment_detail`: enrollment + aggregated prescriber and medication lists (junctions).

## Acceptance
- Views queryable after schema load; columns documented in README or SQL comments.

## Ref
- `plan/medical_app_scenario/PLAN.md` §3.6
'@
  }
  @{
    Title = "[medical] Seed generator and data.sql (≥400 rows + named multi-exemplar fixtures)"
    Body = @'
## Goal
Deterministic seed per PLAN §2, §6 and DEMO.md.

## Named fixtures (**PLAN.md §2.1**)
**At least three distinct patients per scenario**, with realistic first + last names:
- **M1 ALLOW:** Jordan Hayes, Morgan Reed, Taylor Brooks
- **M2 allergy DENY:** Riley Chen, Alex Rivera, Casey Nguyen
- **M3 trial concomitant:** Sam Okonkwo, Jamie Foster, Drew Patel
- **M4 open severe AE:** Avery Morrison, Blake Okada, Dakota Flynn
- **M5 pending review:** Nico Harper, Remy Santos, Sage Lombardi
- **M6 AE reporter / prescriber mismatch:** Lake Kim, Rowan Gupta, Skyler Adams

Include negative controls and varied ages/sites where useful (PLAN §6).

## Edge cases (PLAN §6)
Allergy conflict, trial concomitant violation, pediatric + warning drug, AE reporter aligned (clean) **and** mismatch rows for M6, duplicate therapy, unverified allergy only.

## Deliverables
- `seed/generate_data.py` or generator producing `seed/data.sql`; row counts per PLAN §2 bands; **≥400** inserted lines acceptable.

## Acceptance
- Schema → data load succeeds; spot checks for each §2.1 name; FKs satisfied.

## Ref
- `plan/medical_app_scenario/PLAN.md` §2, §2.1, §6
- `plan/medical_app_scenario/DEMO.md`
'@
  }
  @{
    Title = "[medical] Backend API for Postgres (enrollment junctions, rx, AE, reviews)"
    Body = @'
## Goal
Read/write API; browser does not connect to DB directly (PLAN §4).

## Minimum endpoints
- Patients: list, search, detail (allergies, conditions, enrollments, prescriptions, AEs or views).
- Trials: list, detail, enrollments.
- **POST/PUT enrollment:** patient, trial, site; **multi** prescribers + medications → junction rows (PLAN screen 4).
- Prescriptions: outpatient create (M1/M2 targets for **Jordan Hayes** / **Riley Chen** etc.).
- Adverse events: create with optional `enrollment_id`.
- Enrollment reviews: approve/reject (M5).

## Acceptance
- Create enrollment with 2 prescribers + 2 meds → correct junction rows; prescription for a safe patient (e.g. Jordan Hayes) succeeds.

## Ref
- `plan/medical_app_scenario/PLAN.md` §4
- `plan/medical_app_scenario/SCENARIO.md` tasks M1–M6
'@
  }
  @{
    Title = "[medical] Web UI: Dashboard and Patients (list + detail)"
    Body = @'
## Goal
Iframe-friendly UI (PLAN §4 screens 1–2).

## Screens
1. **Dashboard:** active trials, open AEs, pending reviews.
2. **Patients:** searchable table → detail (allergies, conditions, enrollments, prescriptions, AEs; use `v_patient_timeline` where helpful).

Seed must surface **≥3 names per scenario** from PLAN §2.1 so lists are not single-exemplar.

## Acceptance
- Dashboard counts match SQL on seed data.

## Ref
- `plan/medical_app_scenario/PLAN.md` §4 (1–2), §2.1
'@
  }
  @{
    Title = "[medical] Web UI: Trials, enrollment detail, multi-select enrollment form"
    Body = @'
## Goal
PLAN §4 screens 3–4.

## Screens
3. Trials list → detail + enrollments.
4. Enrollment form: patient, trial, site; **multi-select** prescribers and medications.

## Acceptance
- Create enrollment via UI; DB shows header + junction rows.

## Ref
- `plan/medical_app_scenario/PLAN.md` §4 (3–4)
'@
  }
  @{
    Title = "[medical] Web UI: Prescription, AE, review forms + dev re-seed"
    Body = @'
## Goal
PLAN §4 screens 5–8.

## Screens
5. Prescription form (outpatient).
6. Adverse event form (optional enrollment).
7. Enrollment review approve/reject.
8. **Admin:** re-seed **dev only** (env/build flag).

## Acceptance
- Rx for safe patient; AE for open-AE cohort; review toggle for M5 names; re-seed resets dev DB.

## Ref
- `plan/medical_app_scenario/PLAN.md` §4 (5–8), §2.1
'@
  }
  @{
    Title = "[medical] Tests: psql assertions and API smoke (multi-exemplar fixtures)"
    Body = @'
## Goal
PLAN §7.

## Deliverables
- `tests/test_db.sh` or npm script: FK sanity, row floors, **≥3 rows per PLAN §2.1 category**, presence of exemplar names (e.g. Jordan Hayes, Riley Chen, Sam Okonkwo).
- API smoke: POST enrollment creates junction rows.
- Optional: Playwright prescription flow.

## Acceptance
- Documented command passes on clean DB + seed.

## Ref
- `plan/medical_app_scenario/PLAN.md` §7, §2.1
'@
  }
  @{
    Title = "[medical] TypeQL shadow / plugin (Layer A) — track separately from mini-app"
    Body = @'
## Note
PLAN §8: DDL → TypeQL, PERA-style `trial-enrollment`; `fun` catalog in SCENARIO.md. **Plugin** work — not required to ship the Postgres + web mini-app.

Track integration in this issue or child issues so mini-app milestones stay independently shippable.

## Ref
- `plan/medical_app_scenario/PLAN.md` §8
- `plan/medical_app_scenario/SCENARIO.md` §1–2
'@
  }
)

foreach ($i in $issues) {
  New-GhIssue -Title $i.Title -Body $i.Body
}

Write-Host "Done. Verify with: gh issue list --label medical  (or gh issue list --limit 20)"
