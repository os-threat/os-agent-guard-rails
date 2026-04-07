"use strict";

/**
 * Seeds MongoDB for financial planner demo (plan §3).
 * Run: `node generate_data.js` with MONGODB_URI, or invoked from mock server when AUTO_SEED=true.
 */

const path = require("path");

function loadMongo() {
  return require(require.resolve("mongodb", {
    paths: [path.join(__dirname, "../mock/node_modules")],
  }));
}

const URI = process.env.MONGODB_URI || "mongodb://127.0.0.1:27017/financial_planner";

function rnd(seed, i) {
  const x = Math.sin(seed * 9999 + i) * 10000;
  return x - Math.floor(x);
}

async function run(db) {
  const shouldClose = !db;
  let client;
  if (!db) {
    const { MongoClient } = loadMongo();
    client = new MongoClient(URI);
    await client.connect();
    db = client.db();
  }

  const cols = [
    "clients",
    "accounts",
    "holdings",
    "plans",
    "goals",
    "fee_schedules",
    "disclosures",
    "recommendation_audit",
    "idempotency_keys",
    "trade_preview_audit",
    "executed_trades",
    "wash_sale_events",
  ];
  for (const c of cols) {
    await db.collection(c).deleteMany({});
  }

  const clients = [];
  const n = 62;
  for (let i = 0; i < n; i++) {
    const id = `C-GEN-${String(i).padStart(4, "0")}`;
    const risk = ["conservative", "moderate", "aggressive"][i % 3];
    const kyc = ["retail", "accredited", "qualified"][i % 3];
    clients.push({
      id,
      display_name: `Generated Client ${i}`,
      kyc_tier: kyc,
      risk_tier: risk,
      _id: id,
    });
  }

  clients.push(
    {
      id: "C-ALLOW",
      display_name: "Allow Demo Client",
      kyc_tier: "accredited",
      risk_tier: "moderate",
      _id: "C-ALLOW",
    },
    {
      id: "C-DENY",
      display_name: "Deny Concentration Demo",
      kyc_tier: "accredited",
      risk_tier: "moderate",
      _id: "C-DENY",
    },
    {
      id: "C-NON-ACC",
      display_name: "Retail KYC Demo",
      kyc_tier: "retail",
      risk_tier: "moderate",
      _id: "C-NON-ACC",
    }
  );

  await db.collection("clients").insertMany(clients);

  const accounts = [];
  let aid = 0;
  for (const c of clients) {
    const count = 1 + (aid % 3);
    for (let j = 0; j < count; j++) {
      const types = ["TAXABLE", "IRA", "ROLLOVER_401K"];
      const id = `A-${c.id}-${j}`;
      accounts.push({
        id,
        client_id: c.id,
        type: types[aid % 3],
        nickname: `Account ${j}`,
        _id: id,
      });
      aid += 1;
    }
  }

  await db.collection("accounts").insertMany(accounts);

  const sectors = ["Technology", "Health Care", "Financials", "Consumer", "Industrials"];
  const symbols = ["VTI", "VXUS", "BND", "AAPL", "MSFT", "JPM", "REGD"];

  const holdings = [];
  for (const a of accounts) {
    const hcount = 3 + Math.floor(rnd(a.id.length, 2) * 5);
    for (let k = 0; k < hcount; k++) {
      const sym = symbols[(k + a.id.length) % symbols.length];
      const mv = Math.round(5000 + rnd(a.id.charCodeAt(0), k) * 45000);
      holdings.push({
        _id: `${a.id}:${sym}:${k}`,
        account_id: a.id,
        symbol: sym,
        quantity: Math.round(10 + rnd(3, k) * 200),
        cost_basis_usd: mv * 0.95,
        market_value_usd: mv,
        sector: sectors[(k + sym.length) % sectors.length],
        flags: sym === "REGD" ? ["accredited_only"] : [],
      });
    }
  }

  const allowTax = accounts.find((a) => a.client_id === "C-ALLOW" && a.type === "TAXABLE");
  const denyTax = accounts.find((a) => a.client_id === "C-DENY" && a.type === "TAXABLE");
  const nonAccTax = accounts.find((a) => a.client_id === "C-NON-ACC" && a.type === "TAXABLE");

  function replaceHoldingsFor(accountId, rows) {
    for (let i = holdings.length - 1; i >= 0; i--) {
      if (holdings[i].account_id === accountId) holdings.splice(i, 1);
    }
    for (const r of rows) {
      holdings.push({
        _id: `${accountId}:${r.symbol}`,
        account_id: accountId,
        ...r,
      });
    }
  }

  if (allowTax) {
    const sectors = [
      "Technology",
      "Health Care",
      "Financials",
      "Consumer",
      "Industrials",
      "Energy",
      "Materials",
      "Utilities",
      "Real Estate",
      "Communication",
    ];
    const per = 10000;
    const allowRows = sectors.map((sector, i) => ({
      symbol: `DIV${i + 1}`,
      quantity: 100 + i,
      cost_basis_usd: per * 0.98,
      market_value_usd: per,
      sector,
      flags: [],
    }));
    replaceHoldingsFor(allowTax.id, allowRows);
  }

  if (denyTax) {
    replaceHoldingsFor(denyTax.id, [
      {
        symbol: "AAPL",
        quantity: 500,
        cost_basis_usd: 90000,
        market_value_usd: 120000,
        sector: "Technology",
        flags: [],
      },
      {
        symbol: "CASH",
        quantity: 1,
        cost_basis_usd: 30000,
        market_value_usd: 30000,
        sector: "Cash",
        flags: [],
      },
    ]);
  }

  if (nonAccTax) {
    replaceHoldingsFor(nonAccTax.id, [
      {
        symbol: "VTI",
        quantity: 20,
        cost_basis_usd: 20000,
        market_value_usd: 21000,
        sector: "Technology",
        flags: [],
      },
    ]);
  }

  const iraDeny = accounts.find((a) => a.client_id === "C-DENY" && a.type === "IRA");
  if (iraDeny) {
    holdings.push({
      _id: `${iraDeny.id}:MARGIN`,
      account_id: iraDeny.id,
      symbol: "MARGIN_ETF",
      quantity: 10,
      cost_basis_usd: 1000,
      market_value_usd: 1000,
      sector: "Technology",
      flags: ["margin_only"],
    });
  }

  await db.collection("holdings").insertMany(holdings);

  const plans = [];
  const goals = [];
  for (const c of clients.slice(0, 40)) {
    const pid = `P-${c.id}`;
    plans.push({ id: pid, client_id: c.id, name: `Plan ${c.id}`, _id: pid });
    goals.push({
      id: `G-${c.id}-1`,
      plan_id: pid,
      name: "Education",
      target_date: new Date(Date.now() + 3600 * 24 * 365 * (3 + (c.id.length % 5))).toISOString().slice(0, 10),
      target_amount_usd: 80000,
      _id: `G-${c.id}-1`,
    });
  }

  const allowPlan = { id: "P-C-ALLOW", client_id: "C-ALLOW", name: "Retirement", _id: "P-C-ALLOW" };
  const denyPlan = { id: "P-C-DENY", client_id: "C-DENY", name: "Growth", _id: "P-C-DENY" };
  plans.push(allowPlan, denyPlan);
  goals.push(
    {
      id: "G-ALLOW-1",
      plan_id: allowPlan.id,
      name: "Long horizon",
      target_date: new Date(Date.now() + 3600 * 24 * 365 * 15).toISOString().slice(0, 10),
      target_amount_usd: 500000,
      _id: "G-ALLOW-1",
    },
    {
      id: "G-DENY-1",
      plan_id: denyPlan.id,
      name: "Near-term",
      target_date: new Date(Date.now() + 3600 * 24 * 365 * 2).toISOString().slice(0, 10),
      target_amount_usd: 50000,
      _id: "G-DENY-1",
    }
  );

  await db.collection("plans").insertMany(plans);
  await db.collection("goals").insertMany(goals);

  const feeRows = [
    { id: "F-IRA", account_type: "IRA", description: "IRA custody", rate_bps: 15 },
    { id: "F-TAX", account_type: "TAXABLE", description: "Taxable ticket", rate_bps: 5 },
    { id: "F-401", account_type: "ROLLOVER_401K", description: "Rollover", rate_bps: 10 },
  ];
  await db.collection("fee_schedules").insertMany(feeRows);

  if (allowTax) {
    await db.collection("disclosures").insertOne({
      id: "D-1",
      account_id: allowTax.id,
      disclosure_id: "FEE-2025-01",
      accepted_at: new Date().toISOString(),
      _id: "D-1",
    });
  }

  if (denyTax) {
    await db.collection("wash_sale_events").insertOne({
      account_id: denyTax.id,
      symbol: "VTI",
      loss_sale_at: new Date(Date.now() - 3 * 24 * 3600 * 1000).toISOString(),
      quantity: 5,
    });
  }

  if (shouldClose) await client.close();
  else console.log("[seed] Financial planner demo data loaded.");
}

if (require.main === module) {
  run()
    .then(() => {
      console.log("[seed] Done.");
      process.exit(0);
    })
    .catch((e) => {
      console.error(e);
      process.exit(1);
    });
}

module.exports = { run };
