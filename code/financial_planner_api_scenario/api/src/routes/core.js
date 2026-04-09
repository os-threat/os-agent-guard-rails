"use strict";

const crypto = require("crypto");
const express = require("express");
const { getDb } = require("../services/db");
const { sendProblem } = require("../problem");

const router = express.Router();

function parsePaging(req) {
  const limit = Math.min(Number(req.query.limit || 50), 200);
  const offset = Math.max(Number(req.query.offset || 0), 0);
  return { limit, offset };
}

async function listCollection(req, res, name) {
  const db = getDb();
  const { limit, offset } = parsePaging(req);
  const total = await db.collection(name).countDocuments();
  const items = await db.collection(name).find({}).skip(offset).limit(limit).toArray();
  res.json({ items, total, limit, offset });
}

async function createInCollection(req, res, name, requiredFields) {
  const db = getDb();
  const body = req.body || {};
  for (const f of requiredFields) {
    if (!body[f]) {
      return sendProblem(res, 400, "Bad Request", `Missing required field: ${f}`);
    }
  }
  const doc = {
    id: body.id || crypto.randomUUID(),
    ...body,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
  await db.collection(name).insertOne(doc);
  return res.status(201).json(doc);
}

router.get("/v1/clients", async (req, res, next) => {
  try {
    await listCollection(req, res, "clients");
  } catch (e) {
    next(e);
  }
});

router.post("/v1/clients", async (req, res, next) => {
  try {
    await createInCollection(req, res, "clients", ["first_name", "last_name", "date_of_birth"]);
  } catch (e) {
    next(e);
  }
});

router.get("/v1/clients/:id", async (req, res, next) => {
  try {
    const db = getDb();
    const row = await db.collection("clients").findOne({ id: req.params.id });
    if (!row) return sendProblem(res, 404, "Not Found", "Client not found");
    res.json(row);
  } catch (e) {
    next(e);
  }
});

router.patch("/v1/clients/:id", async (req, res, next) => {
  try {
    const db = getDb();
    const updates = { ...(req.body || {}), updated_at: new Date().toISOString() };
    const result = await db
      .collection("clients")
      .findOneAndUpdate({ id: req.params.id }, { $set: updates }, { returnDocument: "after" });
    if (!result.value) return sendProblem(res, 404, "Not Found", "Client not found");
    res.json(result.value);
  } catch (e) {
    next(e);
  }
});

router.get("/v1/households", async (req, res, next) => {
  try {
    await listCollection(req, res, "households");
  } catch (e) {
    next(e);
  }
});

router.post("/v1/households", async (req, res, next) => {
  try {
    await createInCollection(req, res, "households", ["household_name"]);
  } catch (e) {
    next(e);
  }
});

router.get("/v1/profiles", async (req, res, next) => {
  try {
    await listCollection(req, res, "profiles");
  } catch (e) {
    next(e);
  }
});

router.post("/v1/profiles", async (req, res, next) => {
  try {
    await createInCollection(req, res, "profiles", ["client_id"]);
  } catch (e) {
    next(e);
  }
});

router.get("/v1/important-dates", async (req, res, next) => {
  try {
    await listCollection(req, res, "important_dates");
  } catch (e) {
    next(e);
  }
});

router.post("/v1/important-dates", async (req, res, next) => {
  try {
    await createInCollection(req, res, "important_dates", ["client_id", "date_type", "date_value"]);
  } catch (e) {
    next(e);
  }
});

module.exports = { coreRouter: router };
