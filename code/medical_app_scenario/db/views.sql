CREATE OR REPLACE VIEW v_patient_timeline AS
SELECT
  p.id AS patient_pk,
  p.patient_id,
  p.first_name,
  p.last_name,
  'prescription'::TEXT AS event_type,
  pr.rx_id AS event_id,
  pr.created_at AS event_at,
  pr.status AS event_status,
  m.name AS summary,
  NULL::TEXT AS details
FROM patients p
JOIN prescriptions pr ON pr.patient_id = p.id
JOIN medications m ON m.id = pr.medication_id

UNION ALL

SELECT
  p.id AS patient_pk,
  p.patient_id,
  p.first_name,
  p.last_name,
  'adverse_event'::TEXT AS event_type,
  ae.adverse_event_id AS event_id,
  ae.reported_at AS event_at,
  ae.status AS event_status,
  aet.description AS summary,
  ae.details
FROM patients p
JOIN adverse_events ae ON ae.patient_id = p.id
JOIN adverse_event_types aet ON aet.code = ae.event_type_code

UNION ALL

SELECT
  p.id AS patient_pk,
  p.patient_id,
  p.first_name,
  p.last_name,
  'trial_enrollment'::TEXT AS event_type,
  te.enrollment_id AS event_id,
  te.enrolled_at AS event_at,
  te.status AS event_status,
  t.title AS summary,
  NULL::TEXT AS details
FROM patients p
JOIN trial_enrollments te ON te.patient_id = p.id
JOIN trials t ON t.id = te.trial_id;

CREATE OR REPLACE VIEW v_enrollment_detail AS
SELECT
  te.id AS enrollment_pk,
  te.enrollment_id,
  te.status,
  te.enrolled_at,
  p.patient_id,
  p.first_name || ' ' || p.last_name AS patient_name,
  t.trial_id,
  t.title AS trial_title,
  h.hospital_id AS site_business_id,
  h.name AS site_name,
  COALESCE(
    STRING_AGG(DISTINCT (d.license_id || ':' || d.first_name || ' ' || d.last_name), ', ')
      FILTER (WHERE d.license_id IS NOT NULL),
    ''
  ) AS prescribers,
  COALESCE(
    STRING_AGG(DISTINCT (m.drug_code || ':' || m.name), ', ')
      FILTER (WHERE m.drug_code IS NOT NULL),
    ''
  ) AS enrollment_medications,
  COALESCE(
    STRING_AGG(DISTINCT (am.drug_code || ':' || am.name), ', ')
      FILTER (WHERE am.drug_code IS NOT NULL),
    ''
  ) AS trial_allowed_medications
FROM trial_enrollments te
JOIN patients p ON p.id = te.patient_id
JOIN trials t ON t.id = te.trial_id
LEFT JOIN hospitals h ON h.id = te.site_id
LEFT JOIN trial_enrollment_prescribers tep ON tep.enrollment_id = te.id
LEFT JOIN doctors d ON d.license_id = tep.doctor_license
LEFT JOIN trial_enrollment_medications tem ON tem.enrollment_id = te.id
LEFT JOIN medications m ON m.id = tem.medication_id
LEFT JOIN trial_allowed_medications tam ON tam.trial_id = te.trial_id
LEFT JOIN medications am ON am.id = tam.medication_id
GROUP BY
  te.id,
  te.enrollment_id,
  te.status,
  te.enrolled_at,
  p.patient_id,
  p.first_name,
  p.last_name,
  t.trial_id,
  t.title,
  h.hospital_id,
  h.name;
