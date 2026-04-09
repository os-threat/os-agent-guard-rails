"use strict";

const express = require("express");
const crypto = require("crypto");
const { getDb } = require("../services/db");
const { sendProblem } = require("../problem");
const { attachGetPatch } = require("./crudId");

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

async function createCollection(req, res, name) {
  const db = getDb();
  const body = req.body || {};
  if (
    name === "recommendations" &&
    !body.client_id
  ) {
    return sendProblem(res, 400, "Bad Request", "Missing required field: client_id");
  }
  if (
    name !== "recommendations" &&
    !body.client_id &&
    !body.household_id &&
    !body.segment_id
  ) {
    return sendProblem(
      res,
      400,
      "Bad Request",
      "Provide at least one of: client_id, household_id, segment_id"
    );
  }
  const doc = {
    id: body.id || crypto.randomUUID(),
    ...body,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
  await db.collection(name).insertOne(doc);
  res.status(201).json(doc);
}

const resources = [
  "tasks",
  "communications",
  "campaigns",
  "anniversary-triggers",
  "tax-planning-checkpoints",
  "recommendations"
];

for (const resource of resources) {
  const collection = resource.replace(/-/g, "_");
  const basePath = `/v1/${resource}`;

  router.get(basePath, async (req, res, next) => {
    try {
      await listCollection(req, res, collection);
    } catch (e) {
      next(e);
    }
  });

  router.post(basePath, async (req, res, next) => {
    try {
      await createCollection(req, res, collection);
    } catch (e) {
      next(e);
    }
  });

  attachGetPatch(router, basePath, collection);
}

module.exports = { workflowsRouter: router };
