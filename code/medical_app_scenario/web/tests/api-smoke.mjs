import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { Pool } from "pg";
import dotenv from "dotenv";

dotenv.config({ path: "../.env" });
dotenv.config();

const require = createRequire(import.meta.url);
const app = require("../src/app");

const host = process.env.POSTGRES_HOST || "localhost";
const port = Number(process.env.POSTGRES_PORT || 5433);
const user = process.env.POSTGRES_USER || "medical_app";
const password = process.env.POSTGRES_PASSWORD || "medical_app_dev_pw";
const database = process.env.POSTGRES_DB || "medical_mini_app";
const connectionString =
  process.env.DATABASE_URL || `postgresql://${user}:${password}@${host}:${port}/${database}`;

const pool = new Pool({ connectionString });

function url(base, path) {
  return `${base}${path}`;
}

async function main() {
  const server = await new Promise((resolve) => {
    const s = app.listen(0, () => resolve(s));
  });
  const address = server.address();
  const base = `http://127.0.0.1:${address.port}`;

  try {
    const health = await fetch(url(base, "/health"));
    assert.equal(health.status, 200);
    const healthBody = await health.json();
    assert.equal(healthBody.ok, true);

    const patientsResp = await fetch(url(base, "/patients?search=Jordan%20Hayes"));
    assert.equal(patientsResp.status, 200);
    const patients = await patientsResp.json();
    assert.ok(Array.isArray(patients));
    assert.ok(patients.length >= 1, "Expected Jordan Hayes in seed data");
    const jordan = patients[0];

    const trialsResp = await fetch(url(base, "/trials"));
    assert.equal(trialsResp.status, 200);
    const trials = await trialsResp.json();
    assert.ok(trials.length >= 1, "Expected at least one trial");
    const firstTrial = trials[0];

    const doctorRows = await pool.query("SELECT license_id FROM doctors ORDER BY id LIMIT 2");
    const medRows = await pool.query("SELECT id FROM medications ORDER BY id LIMIT 2");
    const siteRow = await pool.query("SELECT id FROM hospitals ORDER BY id LIMIT 1");

    assert.equal(doctorRows.rowCount, 2);
    assert.equal(medRows.rowCount, 2);
    assert.equal(siteRow.rowCount, 1);

    const enrollmentCreate = await fetch(url(base, "/enrollments"), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        patientId: Number(jordan.id),
        trialId: Number(firstTrial.id),
        siteId: Number(siteRow.rows[0].id),
        prescriberLicenses: [doctorRows.rows[0].license_id, doctorRows.rows[1].license_id],
        medicationIds: [Number(medRows.rows[0].id), Number(medRows.rows[1].id)],
      }),
    });
    assert.equal(enrollmentCreate.status, 201);
    const enrollment = await enrollmentCreate.json();
    assert.ok(enrollment.id, "Expected enrollment id");

    const prescriberCount = await pool.query(
      "SELECT COUNT(*)::INT AS c FROM trial_enrollment_prescribers WHERE enrollment_id = $1",
      [enrollment.id]
    );
    const medCount = await pool.query(
      "SELECT COUNT(*)::INT AS c FROM trial_enrollment_medications WHERE enrollment_id = $1",
      [enrollment.id]
    );
    assert.equal(prescriberCount.rows[0].c, 2);
    assert.equal(medCount.rows[0].c, 2);

    const rxResp = await fetch(url(base, "/prescriptions"), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        patientId: Number(jordan.id),
        prescriberLicense: doctorRows.rows[0].license_id,
        hospitalId: Number(siteRow.rows[0].id),
        medicationId: Number(medRows.rows[0].id),
        dose: "10mg",
        frequency: "daily",
        route: "oral",
      }),
    });
    assert.equal(rxResp.status, 201);
    const rx = await rxResp.json();
    assert.ok(rx.id, "Expected prescription row");

    const dbSanity = await pool.query("SELECT COUNT(*)::INT AS c FROM patients");
    assert.ok(dbSanity.rows[0].c >= 80, "Expected patient row floor");

    console.log("API smoke tests passed");
  } finally {
    server.close();
    await pool.end();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
