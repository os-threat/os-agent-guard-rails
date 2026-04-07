/**
 * Lightweight contract smoke: health + OpenAPI JSON when API is up.
 *   BASE_URL=http://127.0.0.1:8082 node tests/contract_smoke.mjs
 */

const BASE = process.env.BASE_URL || "http://127.0.0.1:8082";

async function main() {
  const health = await fetch(`${BASE}/health`);
  if (!health.ok) {
    console.error("GET /health failed", health.status);
    process.exit(1);
  }
  const specRes = await fetch(`${BASE}/openapi.json`);
  if (!specRes.ok) {
    console.error("GET /openapi.json failed", specRes.status);
    process.exit(1);
  }
  const spec = await specRes.json();
  const paths = Object.keys(spec.paths || {});
  if (paths.length < 5) {
    console.error("OpenAPI paths look empty", paths);
    process.exit(1);
  }
  console.log("contract_smoke ok:", paths.length, "paths");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
