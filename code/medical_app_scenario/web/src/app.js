const express = require("express");
const cors = require("cors");
const path = require("path");
const fs = require("fs/promises");
const { execFile } = require("child_process");
const { query, withTransaction, pool } = require("./db");

const app = express();

app.use(cors());
app.use(express.json());

const publicDir = path.join(__dirname, "..", "public");
app.get("/", (_req, res) => {
  res.sendFile(path.join(publicDir, "index.html"));
});
app.use(
  express.static(publicDir, {
    index: false,
    fallthrough: true,
  })
);

app.get("/health", async (_req, res) => {
  const result = await query("SELECT NOW() AS now");
  res.json({ ok: true, dbTime: result.rows[0].now });
});

app.get("/dashboard", async (_req, res) => {
  const [trials, openAes, pendingReviews] = await Promise.all([
    query("SELECT COUNT(*)::INT AS c FROM trials WHERE status = 'active'"),
    query("SELECT COUNT(*)::INT AS c FROM adverse_events WHERE status = 'open'"),
    query("SELECT COUNT(*)::INT AS c FROM trial_enrollment_reviews WHERE approval_status = 'pending'"),
  ]);
  res.json({
    activeTrials: trials.rows[0].c,
    openAdverseEvents: openAes.rows[0].c,
    pendingReviews: pendingReviews.rows[0].c,
  });
});

app.get("/patients", async (req, res) => {
  const search = (req.query.search || "").trim();
  const params = [];
  let where = "";
  if (search) {
    params.push(`%${search.toLowerCase()}%`);
    where = "WHERE LOWER(p.first_name || ' ' || p.last_name) LIKE $1 OR LOWER(p.patient_id) LIKE $1";
  }

  const result = await query(
    `
      SELECT p.id, p.patient_id, p.first_name, p.last_name, p.date_of_birth
      FROM patients p
      ${where}
      ORDER BY p.last_name, p.first_name
      LIMIT 200
    `,
    params
  );
  res.json(result.rows);
});

app.get("/patients/:id", async (req, res) => {
  const id = Number(req.params.id);
  const patientResult = await query(
    "SELECT id, patient_id, first_name, last_name, date_of_birth FROM patients WHERE id = $1",
    [id]
  );
  if (!patientResult.rowCount) {
    return res.status(404).json({ error: "Patient not found" });
  }

  const [allergies, conditions, timeline, enrollments] = await Promise.all([
    query(
      `
      SELECT a.id, a.allergy_target_type, a.verified, a.reaction, a.severity,
             i.name AS ingredient_name, m.name AS medication_name
      FROM patient_allergies a
      LEFT JOIN ingredients i ON i.id = a.ingredient_id
      LEFT JOIN medications m ON m.id = a.medication_id
      WHERE a.patient_id = $1
      ORDER BY a.id
      `,
      [id]
    ),
    query(
      `
      SELECT condition_code, condition_name, is_active, diagnosed_on, resolved_on
      FROM patient_conditions
      WHERE patient_id = $1
      ORDER BY is_active DESC, condition_name
      `,
      [id]
    ),
    query(
      `
      SELECT event_type, event_id, event_at, event_status, summary, details
      FROM v_patient_timeline
      WHERE patient_pk = $1
      ORDER BY event_at DESC
      LIMIT 200
      `,
      [id]
    ),
    query(
      `
      SELECT enrollment_pk, enrollment_id, status, enrolled_at, trial_id, trial_title,
             site_business_id, site_name, prescribers, enrollment_medications, trial_allowed_medications
      FROM v_enrollment_detail
      WHERE patient_id = (SELECT patient_id FROM patients WHERE id = $1)
      ORDER BY enrolled_at DESC
      `,
      [id]
    ),
  ]);

  return res.json({
    patient: patientResult.rows[0],
    allergies: allergies.rows,
    conditions: conditions.rows,
    timeline: timeline.rows,
    enrollments: enrollments.rows,
  });
});

app.get("/patients/:id/trial-guard", async (req, res) => {
  const patientId = Number(req.params.id);
  if (Number.isNaN(patientId)) {
    return res.status(400).json({ error: "Invalid patient id" });
  }
  const result = await query(
    `
    SELECT
      e.id AS enrollment_pk,
      e.enrollment_id,
      e.status AS enrollment_status,
      t.trial_id,
      t.title AS trial_title,
      COALESCE(
        (
          SELECT r.approval_status
          FROM trial_enrollment_reviews r
          WHERE r.enrollment_id = e.id
          ORDER BY r.id DESC
          LIMIT 1
        ),
        'none'
      ) AS latest_review_status,
      EXISTS (
        SELECT 1
        FROM trial_enrollment_reviews r
        WHERE r.enrollment_id = e.id
          AND r.approval_status = 'pending'
      ) AS has_pending_review
    FROM trial_enrollments e
    JOIN trials t ON t.id = e.trial_id
    WHERE e.patient_id = $1
      AND e.status IN ('active', 'screening')
    ORDER BY e.enrolled_at DESC
    `,
    [patientId]
  );
  const rows = result.rows.map((r) => ({
    enrollmentPk: r.enrollment_pk,
    enrollmentId: r.enrollment_id,
    enrollmentStatus: r.enrollment_status,
    trialId: r.trial_id,
    trialTitle: r.trial_title,
    latestReviewStatus: r.latest_review_status,
    hasPendingReview: r.has_pending_review,
  }));
  const blocksTrialRelatedRx = rows.some((x) => x.hasPendingReview);
  return res.json({ enrollments: rows, blocksTrialRelatedRx });
});

app.get("/trials", async (_req, res) => {
  const result = await query(
    `
      SELECT t.id, t.trial_id, t.title, t.phase, t.status, t.starts_on, t.ends_on,
             COUNT(te.id)::INT AS enrollment_count
      FROM trials t
      LEFT JOIN trial_enrollments te ON te.trial_id = t.id
      GROUP BY t.id
      ORDER BY t.trial_id
    `
  );
  res.json(result.rows);
});

app.get("/trials/:id", async (req, res) => {
  const id = Number(req.params.id);
  const trialResult = await query(
    "SELECT id, trial_id, title, phase, status, starts_on, ends_on FROM trials WHERE id = $1",
    [id]
  );
  if (!trialResult.rowCount) {
    return res.status(404).json({ error: "Trial not found" });
  }
  const enrollmentsResult = await query(
    `
      SELECT e.id, e.enrollment_id, e.status, e.enrolled_at,
             p.id AS patient_pk, p.patient_id, p.first_name, p.last_name,
             h.hospital_id, h.name AS site_name
      FROM trial_enrollments e
      JOIN patients p ON p.id = e.patient_id
      LEFT JOIN hospitals h ON h.id = e.site_id
      WHERE e.trial_id = $1
      ORDER BY e.enrolled_at DESC
    `,
    [id]
  );
  res.json({ trial: trialResult.rows[0], enrollments: enrollmentsResult.rows });
});

app.get("/enrollments", async (_req, res) => {
  const result = await query(
    `
      SELECT e.id, e.enrollment_id, e.status, e.enrolled_at,
             p.id AS patient_pk, p.patient_id, p.first_name, p.last_name,
             t.id AS trial_pk, t.trial_id, t.title AS trial_title,
             h.name AS site_name
      FROM trial_enrollments e
      JOIN patients p ON p.id = e.patient_id
      JOIN trials t ON t.id = e.trial_id
      LEFT JOIN hospitals h ON h.id = e.site_id
      ORDER BY e.enrolled_at DESC
      LIMIT 200
    `
  );
  res.json(result.rows);
});

app.get("/enrollment-reviews", async (req, res) => {
  const statusFilter = req.query.status;
  const params = [];
  let where = "";
  if (statusFilter) {
    params.push(statusFilter);
    where = "WHERE r.approval_status = $1";
  }
  const result = await query(
    `
      SELECT r.id, r.enrollment_id AS enrollment_pk, e.enrollment_id AS enrollment_code, r.reviewer_license,
             r.approval_status, r.reviewed_at, r.review_notes,
             p.first_name, p.last_name, t.trial_id, t.title
      FROM trial_enrollment_reviews r
      JOIN trial_enrollments e ON e.id = r.enrollment_id
      JOIN patients p ON p.id = e.patient_id
      JOIN trials t ON t.id = e.trial_id
      ${where}
      ORDER BY r.created_at DESC
      LIMIT 200
    `,
    params
  );
  res.json(result.rows);
});

app.get("/options", async (_req, res) => {
  const [patients, trials, doctors, medications, hospitals] = await Promise.all([
    query(
      "SELECT id, patient_id, first_name, last_name FROM patients ORDER BY last_name, first_name LIMIT 200"
    ),
    query("SELECT id, trial_id, title FROM trials ORDER BY trial_id"),
    query(
      "SELECT license_id, first_name, last_name, role FROM doctors ORDER BY role, last_name, first_name LIMIT 200"
    ),
    query("SELECT id, drug_code, name FROM medications ORDER BY name LIMIT 300"),
    query("SELECT id, hospital_id, name FROM hospitals ORDER BY name"),
  ]);
  res.json({
    patients: patients.rows,
    trials: trials.rows,
    doctors: doctors.rows,
    medications: medications.rows,
    hospitals: hospitals.rows,
  });
});

app.post("/enrollments", async (req, res) => {
  const { patientId, trialId, siteId = null, prescriberLicenses = [], medicationIds = [] } = req.body;
  if (!patientId || !trialId || prescriberLicenses.length === 0 || medicationIds.length === 0) {
    return res.status(400).json({
      error: "patientId, trialId, at least one prescriberLicense, and at least one medicationId are required",
    });
  }

  const output = await withTransaction(async (tx) => {
    const enrollmentId = `ENR-API-${Date.now()}`;
    const enrollment = await tx.query(
      `
      INSERT INTO trial_enrollments (enrollment_id, patient_id, trial_id, site_id, enrolled_at, status)
      VALUES ($1, $2, $3, $4, NOW(), 'active')
      RETURNING id, enrollment_id, patient_id, trial_id, site_id, status
      `,
      [enrollmentId, patientId, trialId, siteId]
    );

    for (const license of prescriberLicenses) {
      await tx.query(
        `
        INSERT INTO trial_enrollment_prescribers (enrollment_id, doctor_license)
        VALUES ($1, $2)
        `,
        [enrollment.rows[0].id, license]
      );
    }

    for (const medicationId of medicationIds) {
      await tx.query(
        `
        INSERT INTO trial_enrollment_medications (enrollment_id, medication_id)
        VALUES ($1, $2)
        `,
        [enrollment.rows[0].id, medicationId]
      );
    }

    return enrollment.rows[0];
  });

  res.status(201).json(output);
});

app.put("/enrollments/:id", async (req, res) => {
  const enrollmentPk = Number(req.params.id);
  const { status, siteId = null, prescriberLicenses = [], medicationIds = [] } = req.body;

  if (!status) {
    return res.status(400).json({ error: "status is required" });
  }

  const updated = await withTransaction(async (tx) => {
    const enrollmentResult = await tx.query(
      `
      UPDATE trial_enrollments
      SET status = $2, site_id = $3
      WHERE id = $1
      RETURNING id, enrollment_id, patient_id, trial_id, site_id, status
      `,
      [enrollmentPk, status, siteId]
    );
    if (!enrollmentResult.rowCount) {
      return null;
    }

    if (prescriberLicenses.length) {
      await tx.query("DELETE FROM trial_enrollment_prescribers WHERE enrollment_id = $1", [enrollmentPk]);
      for (const license of prescriberLicenses) {
        await tx.query(
          "INSERT INTO trial_enrollment_prescribers (enrollment_id, doctor_license) VALUES ($1, $2)",
          [enrollmentPk, license]
        );
      }
    }

    if (medicationIds.length) {
      await tx.query("DELETE FROM trial_enrollment_medications WHERE enrollment_id = $1", [enrollmentPk]);
      for (const medicationId of medicationIds) {
        await tx.query(
          "INSERT INTO trial_enrollment_medications (enrollment_id, medication_id) VALUES ($1, $2)",
          [enrollmentPk, medicationId]
        );
      }
    }

    return enrollmentResult.rows[0];
  });

  if (!updated) {
    return res.status(404).json({ error: "Enrollment not found" });
  }
  return res.json(updated);
});

app.post("/prescriptions", async (req, res) => {
  const { patientId, prescriberLicense, hospitalId = null, medicationId, dose, frequency, route, startsOn, endsOn, status = "active", isTrialRelated = false } = req.body;
  if (!patientId || !prescriberLicense || !medicationId) {
    return res.status(400).json({ error: "patientId, prescriberLicense, and medicationId are required" });
  }

  const rxId = `RX-API-${Date.now()}`;
  const result = await query(
    `
      INSERT INTO prescriptions (
        rx_id, patient_id, prescriber_license, hospital_id, medication_id,
        dose, frequency, route, starts_on, ends_on, status, is_trial_related
      )
      VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
      RETURNING id, rx_id, patient_id, medication_id, status, created_at
    `,
    [rxId, patientId, prescriberLicense, hospitalId, medicationId, dose || null, frequency || null, route || null, startsOn || null, endsOn || null, status, Boolean(isTrialRelated)]
  );
  res.status(201).json(result.rows[0]);
});

app.post("/adverse-events", async (req, res) => {
  const { patientId, eventTypeCode, reportingPhysicianLicense, enrollmentId = null, severity, status = "open", details = null } = req.body;
  if (!patientId || !eventTypeCode || !reportingPhysicianLicense || !severity) {
    return res
      .status(400)
      .json({ error: "patientId, eventTypeCode, reportingPhysicianLicense, and severity are required" });
  }
  const aeId = `AE-API-${Date.now()}`;
  const result = await query(
    `
      INSERT INTO adverse_events (
        adverse_event_id, patient_id, event_type_code, reporting_physician_license,
        enrollment_id, severity, status, details, reported_at
      )
      VALUES ($1,$2,$3,$4,$5,$6,$7,$8,NOW())
      RETURNING id, adverse_event_id, patient_id, severity, status, reported_at
    `,
    [aeId, patientId, eventTypeCode, reportingPhysicianLicense, enrollmentId, severity, status, details]
  );
  res.status(201).json(result.rows[0]);
});

app.post("/enrollment-reviews", async (req, res) => {
  const { enrollmentId, reviewerLicense, approvalStatus, reviewNotes = null } = req.body;
  if (!enrollmentId || !reviewerLicense || !approvalStatus) {
    return res.status(400).json({ error: "enrollmentId, reviewerLicense, and approvalStatus are required" });
  }
  const reviewedAt = approvalStatus === "pending" ? null : new Date().toISOString();
  const result = await query(
    `
      INSERT INTO trial_enrollment_reviews (enrollment_id, reviewer_license, approval_status, reviewed_at, review_notes)
      VALUES ($1, $2, $3, $4, $5)
      RETURNING id, enrollment_id, reviewer_license, approval_status, reviewed_at
    `,
    [enrollmentId, reviewerLicense, approvalStatus, reviewedAt, reviewNotes]
  );
  res.status(201).json(result.rows[0]);
});

app.put("/enrollment-reviews/:id", async (req, res) => {
  const id = Number(req.params.id);
  const { approvalStatus, reviewNotes = null } = req.body;
  if (!approvalStatus) {
    return res.status(400).json({ error: "approvalStatus is required" });
  }
  const reviewedAt = approvalStatus === "pending" ? null : new Date().toISOString();
  const result = await query(
    `
      UPDATE trial_enrollment_reviews
      SET approval_status = $2, review_notes = $3, reviewed_at = $4
      WHERE id = $1
      RETURNING id, enrollment_id, reviewer_license, approval_status, reviewed_at
    `,
    [id, approvalStatus, reviewNotes, reviewedAt]
  );
  if (!result.rowCount) {
    return res.status(404).json({ error: "Review not found" });
  }
  return res.json(result.rows[0]);
});

app.post("/admin/reseed", async (_req, res) => {
  if (process.env.NODE_ENV === "production") {
    return res.status(403).json({ error: "Admin reseed disabled in production" });
  }

  const rootDir = path.resolve(__dirname, "..", "..");
  const seedDir = path.join(rootDir, "seed");
  const pyScript = path.join(seedDir, "generate_data.py");
  const dataSql = path.join(seedDir, "data.sql");

  await new Promise((resolve, reject) => {
    execFile("python", [pyScript], { cwd: rootDir }, (error, stdout, stderr) => {
      if (error) {
        reject(new Error(`seed generation failed: ${stderr || error.message}`));
        return;
      }
      if (stdout) {
        console.log(stdout.trim());
      }
      resolve();
    });
  });

  const sql = await fs.readFile(dataSql, "utf8");
  await pool.query(sql);
  return res.json({ ok: true, message: "Database reseeded" });
});

app.use((err, _req, res, _next) => {
  console.error(err);
  res.status(500).json({ error: "Internal server error", detail: err.message });
});

module.exports = app;
