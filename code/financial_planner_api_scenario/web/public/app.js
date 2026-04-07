/* global fetch */

function uuid() {
  return crypto.randomUUID();
}

function $(id) {
  return document.getElementById(id);
}

document.querySelectorAll(".tabs button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tabs button").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`panel-${btn.dataset.tab}`).classList.add("active");
  });
});

async function loadDashboard() {
  const el = $("dash-stats");
  el.textContent = "Loading…";
  try {
    const [clients, fees] = await Promise.all([
      fetch("/v1/clients?limit=500").then((r) => r.json()),
      fetch("/v1/fees").then((r) => r.json()),
    ]);
    const accounts = await fetch("/v1/accounts?limit=500").then((r) => r.json());
    let aum = 0;
    for (const a of accounts.items || []) {
      const h = await fetch(`/v1/accounts/${encodeURIComponent(a.id)}/holdings`).then((r) =>
        r.json()
      );
      for (const row of h.items || []) {
        aum += Number(row.market_value_usd) || 0;
      }
    }
    el.innerHTML = "";
    const mk = (title, val) => {
      const d = document.createElement("div");
      d.className = "stat-card";
      d.innerHTML = `<strong>${title}</strong><div>${val}</div>`;
      el.appendChild(d);
    };
    mk("Clients", String(clients.total ?? clients.items?.length ?? "—"));
    mk("Accounts", String(accounts.total ?? accounts.items?.length ?? "—"));
    mk("Mock AUM (sum of holdings)", aum.toLocaleString(undefined, { style: "currency", currency: "USD" }));
    mk("Fee schedules", String(fees.items?.length ?? "—"));
  } catch (e) {
    el.textContent = String(e);
  }
}

$("btn-load-client").addEventListener("click", async () => {
  const id = $("client-id").value.trim();
  $("client-out").textContent = "Loading…";
  try {
    const c = await fetch(`/v1/clients/${encodeURIComponent(id)}`).then((r) => r.json());
    const accts = await fetch(`/v1/accounts?client_id=${encodeURIComponent(id)}`).then((r) =>
      r.json()
    );
    $("tr-acct").value = accts.items?.[0]?.id || "";
    $("client-out").textContent = JSON.stringify({ client: c, accounts: accts }, null, 2);
  } catch (e) {
    $("client-out").textContent = String(e);
  }
});

$("btn-rec").addEventListener("click", async () => {
  $("rec-out").textContent = "…";
  const body = {
    client_id: $("rec-client").value.trim(),
    proposed_symbol: $("rec-symbol").value.trim(),
    dominant_asset_class: $("rec-class").value,
    instrument_requires_accredited: $("rec-acc").checked,
    long_duration_only_stance: $("rec-long").checked,
    horizon_years: Number($("rec-horizon").value) || 10,
  };
  try {
    const res = await fetch("/v1/recommendations", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": uuid(),
      },
      body: JSON.stringify(body),
    });
    const text = await res.text();
    $("rec-out").textContent = `${res.status}\n${text}`;
  } catch (e) {
    $("rec-out").textContent = String(e);
  }
});

let lastPreviewId = null;

$("btn-preview").addEventListener("click", async () => {
  $("trade-out").textContent = "…";
  lastPreviewId = null;
  $("btn-exec").disabled = true;
  const body = {
    preview: true,
    client_id: $("tr-client").value.trim(),
    account_id: $("tr-acct").value.trim(),
    symbol: $("tr-symbol").value.trim(),
    side: "buy",
    quantity: Number($("tr-qty").value) || 1,
    incurs_fee: $("tr-fee").checked,
    session_id: $("tr-session").value.trim() || undefined,
  };
  try {
    const res = await fetch("/v1/trades", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": uuid(),
      },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    $("trade-out").textContent = `${res.status}\n${JSON.stringify(data, null, 2)}`;
    if (res.ok && data.preview_id) {
      lastPreviewId = data.preview_id;
      $("btn-exec").disabled = false;
    }
  } catch (e) {
    $("trade-out").textContent = String(e);
  }
});

$("btn-exec").addEventListener("click", async () => {
  if (!lastPreviewId) return;
  $("trade-out").textContent = "…";
  const body = {
    preview: false,
    preview_id: lastPreviewId,
    client_id: $("tr-client").value.trim(),
    account_id: $("tr-acct").value.trim(),
    symbol: $("tr-symbol").value.trim(),
    side: "buy",
    quantity: Number($("tr-qty").value) || 1,
    incurs_fee: $("tr-fee").checked,
    session_id: $("tr-session").value.trim() || undefined,
  };
  try {
    const res = await fetch("/v1/trades", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": uuid(),
      },
      body: JSON.stringify(body),
    });
    const text = await res.text();
    $("trade-out").textContent = `${res.status}\n${text}`;
  } catch (e) {
    $("trade-out").textContent = String(e);
  }
});

loadDashboard();
