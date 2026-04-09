"use strict";

const express = require("express");
const { getDb } = require("../services/db");
const { config } = require("../config");
const { generateRichDataset } = require("../services/seed");
const { seedScenarioFixtures } = require("../services/fixtures");

const router = express.Router();

router.get("/admin/health", (_req, res) => {
  res.json({ status: "ok", service: "financial-services-api", env: config.env });
});

router.get("/admin/jobs", async (_req, res, next) => {
  try {
    const db = getDb();
    const jobs = await db.collection("admin_jobs").find({}).sort({ created_at: -1 }).limit(100).toArray();
    res.json({ items: jobs, total: jobs.length });
  } catch (e) {
    next(e);
  }
});

router.post("/admin/jobs/seed", async (_req, res, next) => {
  try {
    const result = await generateRichDataset();
    res.status(201).json({ status: "ok", job: "seed_rich_dataset", result });
  } catch (e) {
    next(e);
  }
});

router.post("/admin/jobs/seed-fixtures", async (_req, res, next) => {
  try {
    const result = await seedScenarioFixtures();
    res.status(201).json({ status: "ok", job: "seed_demo_fixtures", result });
  } catch (e) {
    next(e);
  }
});

router.get("/admin/audit", async (_req, res, next) => {
  try {
    const db = getDb();
    const audit = await db.collection("audit_events").find({}).sort({ created_at: -1 }).limit(200).toArray();
    res.json({ items: audit, total: audit.length });
  } catch (e) {
    next(e);
  }
});

router.get("/dashboard/metrics", async (_req, res, next) => {
  try {
    const db = getDb();
    const [active_clients, upcoming_anniversaries, pending_tasks] = await Promise.all([
      db.collection("clients").countDocuments(),
      db.collection("anniversary_triggers").countDocuments(),
      db.collection("tasks").countDocuments({ status: { $ne: "done" } })
    ]);
    res.json({ active_clients, upcoming_anniversaries, pending_tasks });
  } catch (e) {
    next(e);
  }
});

router.get("/admin/integration-contract", (_req, res) => {
  res.json({
    integration_contract: "financial-v2",
    required_headers: ["x-correlation-id"],
    response_metadata: ["_meta.correlation_id", "trace_id for problem+json"],
    notes: "No rules logic is implemented in this mini-app repository."
  });
});

module.exports = { adminRouter: router };
