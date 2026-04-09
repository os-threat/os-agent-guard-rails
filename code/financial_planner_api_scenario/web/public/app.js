(() => {
  const API_BASE = "http://localhost:8082";

  const tabs = [
    {
      id: "dashboard",
      title: "Dashboard",
      help: "Operational summary and KPI snapshot.",
      mode: "dashboard"
    },
    {
      id: "admin",
      title: "Admin",
      help: "Job history and audit records.",
      mode: "admin"
    },
    { id: "clients", title: "Clients", endpoint: "/v1/clients", fields: ["first_name", "last_name", "date_of_birth", "address", "communication_preference"] },
    { id: "households", title: "Households", endpoint: "/v1/households", fields: ["household_name", "primary_client_id"] },
    { id: "profiles", title: "Profiles", endpoint: "/v1/profiles", fields: ["client_id", "risk_tier", "communication_consent", "social_opt_in"] },
    { id: "important-dates", title: "Important Dates", endpoint: "/v1/important-dates", fields: ["client_id", "date_type", "date_value"] },
    { id: "investment-accounts", title: "Investments", endpoint: "/v1/investment-accounts", fields: ["client_id", "product_name"] },
    { id: "savings-accounts", title: "Savings", endpoint: "/v1/savings-accounts", fields: ["client_id", "goal_name", "target_amount", "current_amount"] },
    { id: "super-accounts", title: "Superannuation", endpoint: "/v1/super-accounts", fields: ["client_id", "fund_name"] },
    { id: "insurance-policies", title: "Insurance", endpoint: "/v1/insurance-policies", fields: ["client_id", "insurance_type", "insurer", "premium_annual"] },
    { id: "communications", title: "Communications", endpoint: "/v1/communications", fields: ["client_id", "channel", "outcome"] },
    { id: "campaigns", title: "Campaigns", endpoint: "/v1/campaigns", fields: ["segment_id", "campaign_name", "channel"] },
    { id: "tasks", title: "Tasks & Triggers", endpoint: "/v1/tasks", fields: ["client_id", "task_type", "status", "due_date"] },
    { id: "audit", title: "Audit Activity", endpoint: "/admin/audit", fields: [], readonly: true }
  ];

  const nav = document.getElementById("tab-nav");
  const root = document.getElementById("panel-root");
  const template = document.getElementById("panel-template");
  const healthIndicator = document.getElementById("health-indicator");

  function toInputType(field) {
    if (field.includes("date")) return "date";
    if (field.includes("amount") || field.includes("annual")) return "number";
    return "text";
  }

  function parseBodyFromForm(form, fields) {
    const out = {};
    for (const f of fields) {
      const input = form.querySelector(`[name="${f}"]`);
      if (!input) continue;
      let val = input.value;
      if (val === "") continue;
      if (input.type === "number") {
        const n = Number(val);
        val = Number.isFinite(n) ? n : val;
      }
      if (val === "true") val = true;
      if (val === "false") val = false;
      out[f] = val;
    }
    return out;
  }

  async function callJson(path, opts = {}) {
    const res = await fetch(`${API_BASE}${path}`, opts);
    const text = await res.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
    if (!res.ok) {
      throw new Error(typeof data === "string" ? data : JSON.stringify(data));
    }
    return data;
  }

  async function refreshHealth() {
    try {
      await callJson("/admin/health");
      healthIndicator.className = "status-pill ok";
      healthIndicator.textContent = "API healthy";
    } catch (_e) {
      healthIndicator.className = "status-pill bad";
      healthIndicator.textContent = "API unavailable";
    }
  }

  function makeTabButton(tab) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "tab-btn";
    btn.textContent = tab.title;
    btn.addEventListener("click", () => setActiveTab(tab.id));
    return btn;
  }

  async function renderDashboard(panel, jsonOutput) {
    const formCard = panel.querySelector(".form-card");
    formCard.innerHTML = `
      <h3>Dashboard Metrics</h3>
      <p class="muted small">Metrics are sourced from <code>/dashboard/metrics</code>.</p>
      <div id="dashboard-metrics"></div>
    `;
    const listCard = panel.querySelector(".list-card");
    listCard.innerHTML = `
      <h3>Anniversary Snapshot</h3>
      <div class="list-meta muted small">Preview from <code>/v1/anniversary-triggers</code>.</div>
      <ul class="record-list"></ul>
    `;
    const [metrics, anniversaries] = await Promise.all([
      callJson("/dashboard/metrics"),
      callJson("/v1/anniversary-triggers?limit=12")
    ]);
    const metricsEl = panel.querySelector("#dashboard-metrics");
    metricsEl.innerHTML = `
      <p><strong>Active Clients:</strong> ${metrics.active_clients ?? 0}</p>
      <p><strong>Upcoming Anniversaries:</strong> ${metrics.upcoming_anniversaries ?? 0}</p>
      <p><strong>Pending Tasks:</strong> ${metrics.pending_tasks ?? 0}</p>
    `;
    const ul = panel.querySelector(".record-list");
    ul.innerHTML = (anniversaries.items || []).map((x) => `<li>${x.client_id || "n/a"} - ${x.trigger_type || "trigger"} on ${x.trigger_date || "n/a"}</li>`).join("");
    jsonOutput.textContent = JSON.stringify({ metrics, anniversaries }, null, 2);
  }

  async function renderAdmin(panel, jsonOutput) {
    const formCard = panel.querySelector(".form-card");
    formCard.innerHTML = `
      <h3>Admin Jobs</h3>
      <p class="muted small">Trigger data jobs.</p>
      <div class="form-actions">
        <button type="button" id="seed-rich" class="submit-btn">Run Rich Seed</button>
        <button type="button" id="seed-fix" class="submit-btn">Run Fixture Seed</button>
      </div>
      <pre id="admin-action-result"></pre>
    `;
    const listCard = panel.querySelector(".list-card");
    listCard.innerHTML = `
      <h3>Recent Jobs</h3>
      <ul class="record-list"></ul>
    `;

    const jobs = await callJson("/admin/jobs");
    panel.querySelector(".record-list").innerHTML = (jobs.items || []).map((j) => `<li>${j.job_type} - ${j.status} (${j.created_at || "n/a"})</li>`).join("");

    const actOut = panel.querySelector("#admin-action-result");
    panel.querySelector("#seed-rich").addEventListener("click", async () => {
      actOut.textContent = "Running...";
      try {
        const r = await callJson("/admin/jobs/seed", { method: "POST" });
        actOut.textContent = JSON.stringify(r, null, 2);
      } catch (e) {
        actOut.textContent = String(e);
      }
    });
    panel.querySelector("#seed-fix").addEventListener("click", async () => {
      actOut.textContent = "Running...";
      try {
        const r = await callJson("/admin/jobs/seed-fixtures", { method: "POST" });
        actOut.textContent = JSON.stringify(r, null, 2);
      } catch (e) {
        actOut.textContent = String(e);
      }
    });

    jsonOutput.textContent = JSON.stringify({ jobs }, null, 2);
  }

  async function renderObjectTab(panel, tab, jsonOutput) {
    const form = panel.querySelector(".object-form");
    const submitBtn = panel.querySelector(".submit-btn");
    submitBtn.form = "";
    form.innerHTML = "";

    if (tab.readonly || !tab.fields?.length) {
      form.innerHTML = '<p class="muted small">Read-only view for this tab.</p>';
      submitBtn.style.display = "none";
    } else {
      submitBtn.style.display = "inline-block";
      for (const field of tab.fields) {
        const row = document.createElement("div");
        row.className = "form-row";
        row.innerHTML = `
          <label for="f-${field}">${field}</label>
          <input id="f-${field}" name="${field}" type="${toInputType(field)}" />
        `;
        form.appendChild(row);
      }
      form.id = `form-${tab.id}`;
      submitBtn.form = form.id;
      form.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        const body = parseBodyFromForm(form, tab.fields);
        try {
          await callJson(tab.endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
          });
          await renderObjectTab(panel, tab, jsonOutput);
        } catch (e) {
          alert(`Save failed: ${e}`);
        }
      });
    }

    const response = await callJson(`${tab.endpoint}?limit=50`);
    panel.querySelector(".list-meta").textContent = `Total: ${response.total ?? 0}`;
    panel.querySelector(".record-list").innerHTML = (response.items || []).map((x) => {
      const title = x.id || x.client_id || x.household_name || "record";
      return `<li><strong>${title}</strong><br/>${Object.entries(x).slice(0, 4).map(([k, v]) => `${k}: ${String(v)}`).join(" | ")}</li>`;
    }).join("");
    jsonOutput.textContent = JSON.stringify(response, null, 2);
  }

  async function setActiveTab(tabId) {
    const tab = tabs.find((t) => t.id === tabId) || tabs[0];
    history.replaceState(null, "", `#${tab.id}`);
    nav.querySelectorAll(".tab-btn").forEach((b) => {
      b.classList.toggle("active", b.textContent === tab.title);
    });

    root.innerHTML = "";
    const panel = template.content.firstElementChild.cloneNode(true);
    panel.querySelector(".panel-title").textContent = tab.title;
    panel.querySelector(".panel-help").textContent = tab.help || "Object workspace";
    const refreshBtn = panel.querySelector(".refresh-btn");
    const jsonOutput = panel.querySelector(".json-output");
    root.appendChild(panel);

    const refresh = async () => {
      if (tab.mode === "dashboard") return renderDashboard(panel, jsonOutput);
      if (tab.mode === "admin") return renderAdmin(panel, jsonOutput);
      return renderObjectTab(panel, tab, jsonOutput);
    };
    refreshBtn.addEventListener("click", refresh);
    await refresh();
  }

  function initTabs() {
    nav.innerHTML = "";
    tabs.forEach((tab) => nav.appendChild(makeTabButton(tab)));
  }

  async function init() {
    initTabs();
    await refreshHealth();
    const initial = (location.hash || "").replace(/^#/, "");
    await setActiveTab(initial || "dashboard");
  }

  init().catch((err) => {
    root.innerHTML = `<section class="panel"><p>Failed to initialize UI: ${err}</p></section>`;
  });
})();
