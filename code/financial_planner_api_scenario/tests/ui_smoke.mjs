const WEB_BASE = process.env.WEB_BASE || "http://127.0.0.1:8083";

async function main() {
  const html = await fetch(`${WEB_BASE}/`).then((r) => r.text());
  if (!html.includes("tab-nav")) {
    throw new Error("tab nav missing from UI");
  }
  const appJs = await fetch(`${WEB_BASE}/app.js`);
  if (!appJs.ok) throw new Error("app.js unavailable");
  const styles = await fetch(`${WEB_BASE}/styles.css`);
  if (!styles.ok) throw new Error("styles.css unavailable");
  console.log("ui_smoke: ok");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
