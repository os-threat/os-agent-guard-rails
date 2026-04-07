/**
 * E2E: ALLOW (C-ALLOW) and DENY (C-DENY) for POST /v1/recommendations.
 * Requires API + seeded DB: docker compose up (or npm start + seed).
 *
 *   node tests/e2e_recommendations.mjs
 *   BASE_URL=http://127.0.0.1:8082 node tests/e2e_recommendations.mjs
 */

const BASE = process.env.BASE_URL || "http://127.0.0.1:8082";

function uuid() {
  return globalThis.crypto.randomUUID();
}

async function postJson(path, body, headers = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": uuid(),
      ...headers,
    },
    body: JSON.stringify(body),
  });
  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    data = text;
  }
  return { res, data };
}

async function main() {
  const allowBody = {
    client_id: "C-ALLOW",
    proposed_symbol: "VTI",
    dominant_asset_class: "equity",
    instrument_requires_accredited: false,
    long_duration_only_stance: false,
    horizon_years: 15,
  };
  const denyBody = {
    ...allowBody,
    client_id: "C-DENY",
    proposed_symbol: "AAPL",
  };

  const a = await postJson("/v1/recommendations", allowBody);
  if (a.res.status !== 200 || a.data.guard_status !== "ALLOW") {
    console.error("ALLOW path failed", a.res.status, a.data);
    process.exit(1);
  }
  console.log("ALLOW ok:", a.data);

  const d = await postJson("/v1/recommendations", denyBody);
  if (d.res.status !== 403) {
    console.error("DENY path expected 403", d.res.status, d.data);
    process.exit(1);
  }
  if (!d.data.trace_id) {
    console.error("DENY missing trace_id", d.data);
    process.exit(1);
  }
  console.log("DENY ok (403 + trace_id):", d.data.rule_id, d.data.witness);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
