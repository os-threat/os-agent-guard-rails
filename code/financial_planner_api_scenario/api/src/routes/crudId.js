"use strict";

const { getDb } = require("../services/db");
const { sendProblem } = require("../problem");

function attachGetPatch(router, basePath, collectionName) {
  router.get(`${basePath}/:id`, async (req, res, next) => {
    try {
      const db = getDb();
      const row = await db.collection(collectionName).findOne({ id: req.params.id });
      if (!row) return sendProblem(res, 404, "Not Found", "Record not found");
      res.json(row);
    } catch (e) {
      next(e);
    }
  });

  router.patch(`${basePath}/:id`, async (req, res, next) => {
    try {
      const db = getDb();
      const body = { ...(req.body || {}) };
      delete body.id;
      const updates = { ...body, updated_at: new Date().toISOString() };
      const result = await db
        .collection(collectionName)
        .findOneAndUpdate({ id: req.params.id }, { $set: updates }, { returnDocument: "after" });
      const row = result && typeof result === "object" && "value" in result ? result.value : result;
      if (!row) return sendProblem(res, 404, "Not Found", "Record not found");
      res.json(row);
    } catch (e) {
      next(e);
    }
  });
}

module.exports = { attachGetPatch };
