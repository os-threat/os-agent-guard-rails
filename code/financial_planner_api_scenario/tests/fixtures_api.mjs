/**
 * Fixture-backed API checks for demo clients (plugin demos use same ids).
 * Does not assert FP-R* rule outcomes — those live in the Guardrails plugin.
 */
const BASE = process.env.BASE_URL || "http://127.0.0.1:8082";

async function req(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, opts);
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
  const seed = await req("/admin/jobs/seed-fixtures", { method: "POST" });
  if (!seed.res.ok) throw new Error("seed-fixtures failed");

  for (const id of ["C-FIX-RENEWAL", "C-FIX-TAX", "C-FIX-CAMPAIGN", "C-FIX-COMPLAINT"]) {
    const c = await req(`/v1/clients/${id}`);
    if (!c.res.ok) throw new Error(`missing fixture client ${id}`);
  }

  const addr = await req(`/v1/addresses/ADDR-C-FIX-RENEWAL`);
  if (!addr.res.ok) throw new Error("fixture address missing");

  const rec = await req(`/v1/recommendations/REC-FIX-TAX`);
  if (!rec.res.ok) throw new Error("fixture recommendation missing");

  const taxCreated = await req("/v1/tax-planning-checkpoints", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      client_id: "C-FIX-TAX",
      checkpoint_type: "one_month_pre_tax",
      checkpoint_date: new Date(Date.now() + 25 * 86400000).toISOString().slice(0, 10),
      status: "pending"
    })
  });
  if (!taxCreated.res.ok) throw new Error("tax checkpoint create failed");
  const taxGet = await req(`/v1/tax-planning-checkpoints/${taxCreated.data.id}`);
  if (!taxGet.res.ok) throw new Error("tax checkpoint get by id failed");

  console.log("fixtures_api: ok");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
