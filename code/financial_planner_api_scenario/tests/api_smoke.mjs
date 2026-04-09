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
  const h = await req("/admin/health", {
    headers: {
      "x-correlation-id": "smoke-correlation-id"
    }
  });
  if (!h.res.ok) throw new Error("health failed");
  if (h.res.headers.get("x-correlation-id") !== "smoke-correlation-id") {
    throw new Error("correlation header not propagated");
  }
  if (h.data?._meta?.correlation_id !== "smoke-correlation-id") {
    throw new Error("response metadata missing correlation id");
  }

  const ic = await req("/admin/integration-contract");
  if (!ic.res.ok) throw new Error("integration-contract failed");

  const c = await req("/v1/clients?limit=1");
  if (!c.res.ok) throw new Error("clients list failed");

  const docs = await req("/docs/");
  if (!docs.res.ok) throw new Error("swagger /docs/ failed");

  const oj = await req("/openapi.json");
  if (!oj.res.ok) throw new Error("openapi.json failed");
  if (!oj.data || typeof oj.data !== "object" || !oj.data.openapi) {
    throw new Error("openapi.json not a valid OpenAPI object");
  }

  console.log("api_smoke: ok");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
