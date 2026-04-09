#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f ".env" ]; then
  cp .env.example .env
fi

docker compose up -d
python seed/generate_data.py
cat seed/data.sql | docker compose exec -T postgres psql -U medical_app -d medical_mini_app -v ON_ERROR_STOP=1 >/dev/null

run_scalar() {
  local sql="$1"
  docker compose exec -T postgres psql -U medical_app -d medical_mini_app -t -A -c "$sql" | tr -d '[:space:]'
}

patients="$(run_scalar "select count(*) from patients;")"
allergies="$(run_scalar "select count(*) from patient_allergies;")"
prescriptions="$(run_scalar "select count(*) from prescriptions;")"
enrollments="$(run_scalar "select count(*) from trial_enrollments;")"
adverse_events="$(run_scalar "select count(*) from adverse_events;")"

[ "$patients" -ge 80 ] || { echo "patients floor failed: $patients"; exit 1; }
[ "$allergies" -ge 150 ] || { echo "allergies floor failed: $allergies"; exit 1; }
[ "$prescriptions" -ge 200 ] || { echo "prescriptions floor failed: $prescriptions"; exit 1; }
[ "$enrollments" -ge 40 ] || { echo "enrollments floor failed: $enrollments"; exit 1; }
[ "$adverse_events" -ge 30 ] || { echo "adverse_events floor failed: $adverse_events"; exit 1; }

names_ok="$(run_scalar "select count(*) from patients where (first_name,last_name) in (('Jordan','Hayes'),('Riley','Chen'),('Sam','Okonkwo'),('Avery','Morrison'),('Nico','Harper'),('Lake','Kim'));")"
[ "$names_ok" -eq 6 ] || { echo "fixture name check failed: $names_ok"; exit 1; }

echo "DB assertions passed"
