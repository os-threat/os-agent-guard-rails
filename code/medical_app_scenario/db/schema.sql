BEGIN;

CREATE TABLE IF NOT EXISTS hospitals (
  id BIGSERIAL PRIMARY KEY,
  hospital_id TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  address_line_1 TEXT,
  city TEXT,
  state TEXT,
  postal_code TEXT,
  country TEXT DEFAULT 'US',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS patients (
  id BIGSERIAL PRIMARY KEY,
  patient_id TEXT NOT NULL UNIQUE,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  date_of_birth DATE NOT NULL,
  sex_at_birth TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS doctors (
  id BIGSERIAL PRIMARY KEY,
  license_id TEXT NOT NULL UNIQUE,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('physician', 'pharmacist', 'investigator')),
  specialty TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trials (
  id BIGSERIAL PRIMARY KEY,
  trial_id TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  phase TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  starts_on DATE,
  ends_on DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS drug_classes (
  id BIGSERIAL PRIMARY KEY,
  class_code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL UNIQUE,
  description TEXT
);

CREATE TABLE IF NOT EXISTS medications (
  id BIGSERIAL PRIMARY KEY,
  drug_code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  drug_class_id BIGINT REFERENCES drug_classes(id),
  warning_text TEXT,
  pediatric_warning BOOLEAN NOT NULL DEFAULT FALSE,
  is_controlled_substance BOOLEAN NOT NULL DEFAULT FALSE,
  trial_restricted BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ingredients (
  id BIGSERIAL PRIMARY KEY,
  ingredient_code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS medication_ingredients (
  medication_id BIGINT NOT NULL REFERENCES medications(id) ON DELETE CASCADE,
  ingredient_id BIGINT NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
  PRIMARY KEY (medication_id, ingredient_id)
);

CREATE TABLE IF NOT EXISTS adverse_event_types (
  code TEXT PRIMARY KEY,
  description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS patient_conditions (
  id BIGSERIAL PRIMARY KEY,
  patient_id BIGINT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  condition_code TEXT NOT NULL,
  condition_name TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  diagnosed_on DATE,
  resolved_on DATE,
  UNIQUE (patient_id, condition_code, diagnosed_on)
);

CREATE TABLE IF NOT EXISTS patient_allergies (
  id BIGSERIAL PRIMARY KEY,
  patient_id BIGINT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  allergy_target_type TEXT NOT NULL CHECK (allergy_target_type IN ('ingredient', 'medication')),
  ingredient_id BIGINT REFERENCES ingredients(id),
  medication_id BIGINT REFERENCES medications(id),
  reaction TEXT,
  severity TEXT,
  verified BOOLEAN NOT NULL DEFAULT FALSE,
  noted_on DATE,
  CHECK (
    (allergy_target_type = 'ingredient' AND ingredient_id IS NOT NULL AND medication_id IS NULL) OR
    (allergy_target_type = 'medication' AND medication_id IS NOT NULL AND ingredient_id IS NULL)
  )
);

CREATE TABLE IF NOT EXISTS medication_contraindications (
  id BIGSERIAL PRIMARY KEY,
  medication_id BIGINT NOT NULL REFERENCES medications(id) ON DELETE CASCADE,
  condition_code TEXT,
  min_age_years INTEGER,
  max_age_years INTEGER,
  contraindication_level TEXT NOT NULL DEFAULT 'absolute' CHECK (contraindication_level IN ('absolute', 'relative')),
  notes TEXT
);

CREATE TABLE IF NOT EXISTS prescriptions (
  id BIGSERIAL PRIMARY KEY,
  rx_id TEXT NOT NULL UNIQUE,
  patient_id BIGINT NOT NULL REFERENCES patients(id),
  prescriber_license TEXT NOT NULL REFERENCES doctors(license_id),
  hospital_id BIGINT REFERENCES hospitals(id),
  medication_id BIGINT NOT NULL REFERENCES medications(id),
  dose TEXT,
  frequency TEXT,
  route TEXT,
  starts_on DATE,
  ends_on DATE,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('draft', 'active', 'paused', 'stopped', 'cancelled')),
  is_trial_related BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trial_enrollments (
  id BIGSERIAL PRIMARY KEY,
  enrollment_id TEXT NOT NULL UNIQUE,
  patient_id BIGINT NOT NULL REFERENCES patients(id),
  trial_id BIGINT NOT NULL REFERENCES trials(id),
  site_id BIGINT REFERENCES hospitals(id),
  enrolled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('screening', 'active', 'paused', 'withdrawn', 'completed'))
);

CREATE TABLE IF NOT EXISTS trial_enrollment_prescribers (
  enrollment_id BIGINT NOT NULL REFERENCES trial_enrollments(id) ON DELETE CASCADE,
  doctor_license TEXT NOT NULL REFERENCES doctors(license_id),
  PRIMARY KEY (enrollment_id, doctor_license)
);

CREATE TABLE IF NOT EXISTS trial_enrollment_medications (
  enrollment_id BIGINT NOT NULL REFERENCES trial_enrollments(id) ON DELETE CASCADE,
  medication_id BIGINT NOT NULL REFERENCES medications(id),
  PRIMARY KEY (enrollment_id, medication_id)
);

CREATE TABLE IF NOT EXISTS trial_allowed_medications (
  trial_id BIGINT NOT NULL REFERENCES trials(id) ON DELETE CASCADE,
  medication_id BIGINT NOT NULL REFERENCES medications(id),
  PRIMARY KEY (trial_id, medication_id)
);

CREATE TABLE IF NOT EXISTS trial_enrollment_reviews (
  id BIGSERIAL PRIMARY KEY,
  enrollment_id BIGINT NOT NULL REFERENCES trial_enrollments(id) ON DELETE CASCADE,
  reviewer_license TEXT NOT NULL REFERENCES doctors(license_id),
  approval_status TEXT NOT NULL CHECK (approval_status IN ('pending', 'approved', 'rejected')),
  reviewed_at TIMESTAMPTZ,
  review_notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS adverse_events (
  id BIGSERIAL PRIMARY KEY,
  adverse_event_id TEXT NOT NULL UNIQUE,
  patient_id BIGINT NOT NULL REFERENCES patients(id),
  event_type_code TEXT NOT NULL REFERENCES adverse_event_types(code),
  reporting_physician_license TEXT NOT NULL REFERENCES doctors(license_id),
  enrollment_id BIGINT REFERENCES trial_enrollments(id),
  severity SMALLINT NOT NULL CHECK (severity BETWEEN 1 AND 5),
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'closed')),
  details TEXT,
  reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_doctors_role ON doctors(role);
CREATE INDEX IF NOT EXISTS idx_medications_class ON medications(drug_class_id);
CREATE INDEX IF NOT EXISTS idx_conditions_patient_active ON patient_conditions(patient_id, is_active);
CREATE INDEX IF NOT EXISTS idx_allergies_patient_verified ON patient_allergies(patient_id, verified);
CREATE INDEX IF NOT EXISTS idx_contraindications_med ON medication_contraindications(medication_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_patient_status ON prescriptions(patient_id, status);
CREATE INDEX IF NOT EXISTS idx_trial_enrollments_patient_status ON trial_enrollments(patient_id, status);
CREATE INDEX IF NOT EXISTS idx_trial_reviews_enrollment_status ON trial_enrollment_reviews(enrollment_id, approval_status);
CREATE INDEX IF NOT EXISTS idx_ae_patient_status_severity ON adverse_events(patient_id, status, severity);
CREATE INDEX IF NOT EXISTS idx_ae_enrollment ON adverse_events(enrollment_id);

COMMIT;
