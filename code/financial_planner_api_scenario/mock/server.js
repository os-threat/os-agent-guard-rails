"use strict";

const path = require("path");
const fs = require("fs");
const express = require("express");
const cors = require("cors");
const swaggerUi = require("swagger-ui-express");
const YAML = require("yaml");
const { MongoClient } = require("mongodb");
const { v4: uuidv4 } = require("uuid");
require("dotenv").config({ path: path.join(__dirname, ".env") });

const { problem } = require("./lib/errors");
const rules = require("./lib/rules");

const PORT = Number(process.env.PORT || 8082);
const MONGODB_URI = process.env.MONGODB_URI || "mongodb://127.0.0.1:27017/financial_planner";
const OPENAPI_SPEC = process.env.OPENAPI_SPEC || path.join(__dirname, "..", "openapi", "financial-planner.yaml");
const AUTO_SEED = String(process.env.AUTO_SEED || "").toLowerCase() === "true";

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function loadSpec() {
  const raw = fs.readFileSync(OPENAPI_SPEC, "utf8");
  return YAML.parse(raw);
}

function asyncHandler(fn) {
  return (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
}

async function runSeedIfNeeded(db) {
  if (!AUTO_SEED) return;
  try {
    const { run } = require(path.join(__dirname, "..", "seed", "generate_data.js"));
    await run(db);
    console.log("[fp-mini] AUTO_SEED completed.");
  } catch (e) {
    console.warn("[fp-mini] AUTO_SEED failed:", e.message);
  }
}

async function main() {
  const spec = loadSpec();
  const app = express();
  app.use(cors({ origin: true, credentials: true }));
  app.use(express.json({ limit: "1mb" }));

  app.get("/health", (_req, res) => {
    res.json({ status: "ok" });
  });

  app.get("/openapi.json", (_req, res) => {
    res.json(spec);
  });
  app.use(
    "/docs",
    swaggerUi.serve,
    swaggerUi.setup(spec, { customSiteTitle: "Financial Planner API" })
  );

  const webPublic = path.join(__dirname, "..", "web", "public");
  if (fs.existsSync(webPublic)) {
    app.use(express.static(webPublic));
  }

  const client = new MongoClient(MONGODB_URI);
  await client.connect();
  const db = client.db();

  await runSeedIfNeeded(db);

  const v1 = express.Router();

  function idempotencyHeader(req, res) {
    const key = req.get("Idempotency-Key");
    if (!key || !UUID_RE.test(key)) {
      problem(res, 400, "Bad Request", "Idempotency-Key header must be a UUID v4 (FP-R06).", {
        rule_id: "FP-R06",
      });
      return null;
    }
    return key;
  }

  async function getCachedIdempotency(key, route) {
    const row = await db.collection("idempotency_keys").findOne({ key, route });
    return row;
  }

  async function saveIdempotency(key, route, status, payload) {
    await db.collection("idempotency_keys").updateOne(
      { key, route },
      { $set: { key, route, status, payload, saved_at: new Date() } },
      { upsert: true }
    );
  }

  v1.get(
    "/clients",
    asyncHandler(async (req, res) => {
      const limit = Math.min(Number(req.query.limit) || 100, 500);
      const offset = Number(req.query.offset) || 0;
      const total = await db.collection("clients").countDocuments();
      const items = await db
        .collection("clients")
        .find({})
        .skip(offset)
        .limit(limit)
        .toArray();
      res.json({ items, total });
    })
  );

  v1.post(
    "/clients",
    asyncHandler(async (req, res) => {
      const body = req.body || {};
      if (!body.id) return problem(res, 400, "Bad Request", "id is required");
      const exists = await db.collection("clients").findOne({ id: body.id });
      if (exists) return problem(res, 409, "Conflict", "Client id already exists");
      const doc = { ...body, _id: body.id };
      await db.collection("clients").insertOne(doc);
      res.status(201).json(doc);
    })
  );

  v1.get(
    "/clients/:id",
    asyncHandler(async (req, res) => {
      const c = await db.collection("clients").findOne({ id: req.params.id });
      if (!c) return problem(res, 404, "Not Found", "Client not found");
      res.json(c);
    })
  );

  v1.patch(
    "/clients/:id",
    asyncHandler(async (req, res) => {
      const r = await db
        .collection("clients")
        .findOneAndUpdate(
          { id: req.params.id },
          { $set: req.body || {} },
          { returnDocument: "after" }
        );
      if (!r.value) return problem(res, 404, "Not Found", "Client not found");
      res.json(r.value);
    })
  );

  v1.get(
    "/accounts",
    asyncHandler(async (req, res) => {
      const q = {};
      if (req.query.client_id) q.client_id = req.query.client_id;
      const limit = Math.min(Number(req.query.limit) || 100, 500);
      const offset = Number(req.query.offset) || 0;
      const total = await db.collection("accounts").countDocuments(q);
      const items = await db
        .collection("accounts")
        .find(q)
        .skip(offset)
        .limit(limit)
        .toArray();
      res.json({ items, total });
    })
  );

  v1.post(
    "/accounts",
    asyncHandler(async (req, res) => {
      const body = req.body || {};
      await db.collection("accounts").insertOne({ ...body, _id: body.id });
      res.status(201).json(body);
    })
  );

  v1.get(
    "/accounts/:accountId/holdings",
    asyncHandler(async (req, res) => {
      const account = await db.collection("accounts").findOne({ id: req.params.accountId });
      if (!account) return problem(res, 404, "Not Found", "Account not found");
      const q = { account_id: req.params.accountId };
      const items = await db.collection("holdings").find(q).toArray();
      res.json({ items, total: items.length });
    })
  );

  v1.post(
    "/accounts/:accountId/holdings",
    asyncHandler(async (req, res) => {
      const account = await db.collection("accounts").findOne({ id: req.params.accountId });
      if (!account) return problem(res, 404, "Not Found", "Account not found");
      const body = { ...(req.body || {}), account_id: req.params.accountId };
      await db.collection("holdings").insertOne({ _id: `${body.account_id}:${body.symbol}`, ...body });
      res.status(201).json(body);
    })
  );

  v1.get(
    "/plans",
    asyncHandler(async (req, res) => {
      const q = {};
      if (req.query.client_id) q.client_id = req.query.client_id;
      const items = await db.collection("plans").find(q).toArray();
      res.json({ items, total: items.length });
    })
  );

  v1.post(
    "/plans",
    asyncHandler(async (req, res) => {
      const body = req.body || {};
      await db.collection("plans").insertOne({ ...body, _id: body.id });
      res.status(201).json(body);
    })
  );

  v1.get(
    "/plans/:planId/goals",
    asyncHandler(async (req, res) => {
      const plan = await db.collection("plans").findOne({ id: req.params.planId });
      if (!plan) return problem(res, 404, "Not Found", "Plan not found");
      const items = await db.collection("goals").find({ plan_id: req.params.planId }).toArray();
      res.json({ items, total: items.length });
    })
  );

  v1.post(
    "/plans/:planId/goals",
    asyncHandler(async (req, res) => {
      const plan = await db.collection("plans").findOne({ id: req.params.planId });
      if (!plan) return problem(res, 404, "Not Found", "Plan not found");
      const body = { ...(req.body || {}), plan_id: req.params.planId };
      await db.collection("goals").insertOne({ ...body, _id: body.id });
      res.status(201).json(body);
    })
  );

  v1.post(
    "/recommendations",
    asyncHandler(async (req, res) => {
      const key = idempotencyHeader(req, res);
      if (!key) return;
      const route = "POST /v1/recommendations";
      const cached = await getCachedIdempotency(key, route);
      if (cached?.payload) {
        if ((cached.status || 200) >= 400) {
          res.type("application/problem+json");
        }
        res.status(cached.status || 200).json(cached.payload);
        return;
      }

      const body = req.body || {};
      const client = await db.collection("clients").findOne({ id: body.client_id });
      if (!client) return problem(res, 404, "Not Found", "Client not found");

      const accounts = await db.collection("accounts").find({ client_id: body.client_id }).toArray();
      const accountIds = accounts.map((a) => a.id);
      const holdingsForAccounts = await db
        .collection("holdings")
        .find({ account_id: { $in: accountIds } })
        .toArray();

      const plans = await db.collection("plans").find({ client_id: body.client_id }).toArray();
      const planIds = plans.map((p) => p.id);
      const goals =
        planIds.length === 0
          ? []
          : await db
              .collection("goals")
              .find({ plan_id: { $in: planIds } })
              .toArray();

      const result = rules.evaluateRecommendation({
        client,
        holdingsForAccounts,
        goals,
        body,
      });

      if (result.guard_status === "DENY") {
        const payload = problem(res, 403, "Forbidden", `Policy denial (${result.rule_id})`, {
          rule_id: result.rule_id,
          witness: result.witness,
        });
        await saveIdempotency(key, route, 403, payload);
        await db.collection("recommendation_audit").insertOne({
          client_id: body.client_id,
          proposed_symbol: body.proposed_symbol,
          guard_status: "DENY",
          rule_id: result.rule_id,
          witness: result.witness,
          at: new Date(),
        });
        return;
      }

      const ok = {
        guard_status: "ALLOW",
        client_id: body.client_id,
        proposed_symbol: body.proposed_symbol,
        notes: "Recommendation passed demo guard rules.",
      };
      await db.collection("recommendation_audit").insertOne({
        client_id: body.client_id,
        proposed_symbol: body.proposed_symbol,
        guard_status: "ALLOW",
        at: new Date(),
      });
      res.json(ok);
      await saveIdempotency(key, route, 200, ok);
    })
  );

  v1.post(
    "/trades",
    asyncHandler(async (req, res) => {
      const key = idempotencyHeader(req, res);
      if (!key) return;
      const route = "POST /v1/trades";
      const cached = await getCachedIdempotency(key, route);
      if (cached?.payload) {
        if ((cached.status || 200) >= 400) {
          res.type("application/problem+json");
        }
        res.status(cached.status || 200).json(cached.payload);
        return;
      }

      const body = req.body || {};
      const client = await db.collection("clients").findOne({ id: body.client_id });
      if (!client) return problem(res, 404, "Not Found", "Client not found");
      const account = await db.collection("accounts").findOne({ id: body.account_id });
      if (!account || account.client_id !== body.client_id) {
        return problem(res, 404, "Not Found", "Account not found for client");
      }

      if (body.preview === true) {
        const preview_id = uuidv4();
        await db.collection("trade_preview_audit").insertOne({
          preview_id,
          client_id: body.client_id,
          account_id: body.account_id,
          symbol: body.symbol,
          side: body.side,
          quantity: body.quantity,
          session_id: body.session_id || null,
          incurs_fee: !!body.incurs_fee,
          created_at: new Date(),
        });
        const ok = { status: "preview_created", preview_id };
        res.json(ok);
        await saveIdempotency(key, route, 200, ok);
        return;
      }

      if (!body.preview_id) {
        return problem(res, 422, "Unprocessable Entity", "preview_id required for execute (FP-R05).", {
          rule_id: "FP-R05",
        });
      }

      const prev = await db.collection("trade_preview_audit").findOne({ preview_id: body.preview_id });
      if (!prev || prev.account_id !== body.account_id || prev.symbol !== body.symbol) {
        return problem(res, 403, "Forbidden", "No matching preview for account/symbol (FP-R05).", {
          rule_id: "FP-R05",
        });
      }
      const ps = prev.session_id || null;
      const bs = body.session_id || null;
      if (ps && bs && ps !== bs) {
        return problem(res, 403, "Forbidden", "Session mismatch for preview (FP-R05).", {
          rule_id: "FP-R05",
        });
      }

      if (body.incurs_fee) {
        const since = new Date();
        since.setDate(since.getDate() - rules.FEE_DISCLOSURE_WINDOW_DAYS);
        const disc = await db.collection("disclosures").findOne({
          account_id: body.account_id,
          accepted_at: { $gte: since.toISOString() },
        });
        if (!disc) {
          return problem(res, 403, "Forbidden", "Fee disclosure not accepted within policy window (FP-R04).", {
            rule_id: "FP-R04",
          });
        }
      }

      if (body.side === "buy") {
        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - rules.WASH_SALE_DAYS);
        const wash = await db.collection("wash_sale_events").findOne({
          account_id: body.account_id,
          symbol: body.symbol,
          loss_sale_at: { $gte: cutoff },
        });
        if (wash) {
          return problem(res, 403, "Forbidden", "Wash-sale window violation (FP-R07).", {
            rule_id: "FP-R07",
            witness: { loss_sale_at: wash.loss_sale_at },
          });
        }
      }

      if (account.type === "IRA") {
        const holding = await db.collection("holdings").findOne({
          account_id: body.account_id,
          symbol: body.symbol,
        });
        const flags = holding?.flags || [];
        if (flags.includes("margin_only")) {
          return problem(res, 403, "Forbidden", "IRA cannot hold margin-only instrument (FP-R08).", {
            rule_id: "FP-R08",
          });
        }
      }

      const start = new Date();
      start.setHours(0, 0, 0, 0);
      const count = await db.collection("executed_trades").countDocuments({
        client_id: body.client_id,
        executed_at: { $gte: start },
      });
      if (count >= rules.DAILY_TRADE_CAP) {
        return problem(res, 403, "Forbidden", "Daily trade cap exceeded (FP-R11).", {
          rule_id: "FP-R11",
          witness: { cap: rules.DAILY_TRADE_CAP, count },
        });
      }

      const trade_id = uuidv4();
      await db.collection("executed_trades").insertOne({
        id: trade_id,
        client_id: body.client_id,
        account_id: body.account_id,
        symbol: body.symbol,
        side: body.side,
        quantity: body.quantity,
        executed_at: new Date(),
      });

      const ok = { status: "executed", trade_id };
      res.json(ok);
      await saveIdempotency(key, route, 200, ok);
    })
  );

  v1.get(
    "/fees",
    asyncHandler(async (req, res) => {
      const q = {};
      if (req.query.account_type) q.account_type = req.query.account_type;
      const items = await db.collection("fee_schedules").find(q).toArray();
      res.json({ items });
    })
  );

  v1.post(
    "/documents",
    asyncHandler(async (req, res) => {
      const body = req.body || {};
      const id = uuidv4();
      const doc = { id, ...body };
      await db.collection("disclosures").insertOne({ ...doc, _id: id });
      res.status(201).json(doc);
    })
  );

  app.use("/v1", v1);

  app.use((err, _req, res, _next) => {
    console.error(err);
    problem(res, 500, "Internal Server Error", err.message || "Unexpected error");
  });

  app.listen(PORT, () => {
    console.log(`Financial planner mock listening on http://0.0.0.0:${PORT}`);
    console.log(`OpenAPI: http://localhost:${PORT}/openapi.json  Swagger: http://localhost:${PORT}/docs`);
  });
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
