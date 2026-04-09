/**
 * Multi-step API journey: fixtures, cross-product reads, task create, admin replay surface.
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
  const fx = await req("/admin/jobs/seed-fixtures", { method: "POST" });
  if (!fx.res.ok) throw new Error("seed-fixtures failed");

  const renewal = await req("/v1/clients/C-FIX-RENEWAL");
  if (!renewal.res.ok) throw new Error("renewal client");

  const pol = await req("/v1/insurance-policies/POL-FIX-1");
  if (!pol.res.ok) throw new Error("expected insurance policy fixture POL-FIX-1");

  const renCreate = await req("/v1/insurance-renewals", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      client_id: "C-FIX-RENEWAL",
      policy_id: "POL-FIX-1",
      renewal_date: new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10),
      status: "upcoming"
    })
  });
  if (!renCreate.res.ok) throw new Error("create renewal failed");
  const ren = await req(`/v1/insurance-renewals/${renCreate.data.id}`);
  if (!ren.res.ok) throw new Error("expected renewal row");

  const rec = await req("/v1/recommendations/REC-FIX-RENEWAL");
  if (!rec.res.ok) throw new Error("expected recommendation for renewal fixture");

  const taskBody = {
    client_id: "C-FIX-TAX",
    task_type: "tax_window_follow_up",
    status: "pending",
    due_date: new Date(Date.now() + 5 * 86400000).toISOString().slice(0, 10)
  };
  const created = await req("/v1/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-correlation-id": "journey-1" },
    body: JSON.stringify(taskBody)
  });
  if (!created.res.ok) throw new Error("create task failed");

  const got = await req(`/v1/tasks/${created.data.id}`);
  if (!got.res.ok) throw new Error("get task by id failed");

  const inv = await req("/v1/investment-accounts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_id: "C-FIX-TAX", product_name: "Journey fund" })
  });
  if (!inv.res.ok) throw new Error("create investment account failed");
  const patch = await req(`/v1/investment-accounts/${inv.data.id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_name: "Patched for journey test" })
  });
  if (!patch.res.ok) throw new Error("patch investment account failed");

  const audit = await req("/admin/audit?limit=20");
  if (!audit.res.ok) throw new Error("audit");
  if (!(audit.data.items || []).length) throw new Error("expected audit rows after seed");

  console.log("api_journey: ok");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
