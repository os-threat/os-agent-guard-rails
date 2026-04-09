(() => {
  function getApiBaseUrl() {
    if (typeof window.__FIN_API_BASE__ === "string" && window.__FIN_API_BASE__.trim()) {
      return window.__FIN_API_BASE__.replace(/\/$/, "");
    }
    const qp = new URLSearchParams(window.location.search).get("api");
    if (qp) return qp.replace(/\/$/, "");
    if (!window.location.hostname) return "http://127.0.0.1:8082";
    const port = window.location.port;
    if (port === "8083") {
      return `${window.location.origin}/api`.replace(/\/$/, "");
    }
    return `http://${window.location.hostname}:8082`;
  }

  const tabs = [
    {
      id: "dashboard",
      title: "Dashboard",
      help: "Operational summary, KPI snapshot, and obligation timeline.",
      mode: "dashboard"
    },
    {
      id: "admin",
      title: "Admin",
      help: "Job history and audit records.",
      mode: "admin"
    },
    {
      id: "clients",
      title: "Clients",
      endpoint: "/v1/clients",
      fields: ["first_name", "last_name", "date_of_birth", "address", "communication_preference"],
      quickActions: true
    },
    { id: "households", title: "Households", endpoint: "/v1/households", fields: ["household_name", "primary_client_id"] },
    {
      id: "addresses",
      title: "Addresses",
      endpoint: "/v1/addresses",
      fields: ["client_id", "line1", "suburb", "state", "postcode", "country"]
    },
    { id: "profiles", title: "Profiles", endpoint: "/v1/profiles", fields: ["client_id", "risk_tier", "communication_consent", "social_opt_in"] },
    { id: "important-dates", title: "Important Dates", endpoint: "/v1/important-dates", fields: ["client_id", "date_type", "date_value"] },
    { id: "investment-accounts", title: "Investments", endpoint: "/v1/investment-accounts", fields: ["client_id", "product_name"] },
    { id: "savings-accounts", title: "Savings", endpoint: "/v1/savings-accounts", fields: ["client_id", "goal_name", "target_amount", "current_amount"] },
    { id: "super-accounts", title: "Superannuation", endpoint: "/v1/super-accounts", fields: ["client_id", "fund_name"] },
    { id: "insurance-policies", title: "Insurance", endpoint: "/v1/insurance-policies", fields: ["client_id", "insurance_type", "insurer", "premium_annual"] },
    { id: "communications", title: "Communications", endpoint: "/v1/communications", fields: ["client_id", "channel", "outcome"] },
    { id: "campaigns", title: "Campaigns", endpoint: "/v1/campaigns", fields: ["segment_id", "campaign_name", "channel"] },
    {
      id: "recommendations",
      title: "Recommendations",
      endpoint: "/v1/recommendations",
      fields: ["client_id", "title", "rationale", "status"]
    },
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
    const base = getApiBaseUrl();
    const res = await fetch(`${base}${path}`, opts);
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

  function timelineSortKey(isoDate) {
    if (!isoDate || typeof isoDate !== "string") return "9999-12-31";
    return isoDate.slice(0, 10);
  }

  async function renderDashboard(panel, jsonOutput) {
    const formCard = panel.querySelector(".form-card");
    formCard.innerHTML = `
      <h3>Dashboard Metrics</h3>
      <p class="muted small">Metrics from <code>/dashboard/metrics</code>. API base: <code id="api-base-hint"></code></p>
      <div id="dashboard-metrics"></div>
    `;
    panel.querySelector("#api-base-hint").textContent = getApiBaseUrl();

    const listCard = panel.querySelector(".list-card");
    listCard.innerHTML = `
      <h3>Obligation timeline</h3>
      <p class="list-meta muted small">Merged important dates, anniversary triggers, and tax checkpoints (next 25 by date).</p>
      <ol class="timeline" id="dash-timeline"></ol>
    `;

    const [metrics, importantDates, anniversaries, taxCp] = await Promise.all([
      callJson("/dashboard/metrics"),
      callJson("/v1/important-dates?limit=500"),
      callJson("/v1/anniversary-triggers?limit=500"),
      callJson("/v1/tax-planning-checkpoints?limit=500")
    ]);

    const metricsEl = panel.querySelector("#dashboard-metrics");
    metricsEl.innerHTML = `
      <p><strong>Active Clients:</strong> ${metrics.active_clients ?? 0}</p>
      <p><strong>Anniversary Triggers (rows):</strong> ${metrics.upcoming_anniversaries ?? 0}</p>
      <p><strong>Pending Tasks:</strong> ${metrics.pending_tasks ?? 0}</p>
    `;

    const events = [];
    for (const x of importantDates.items || []) {
      events.push({
        sort: timelineSortKey(x.date_value),
        line: `${x.date_value || "?"} — Important date <strong>${x.date_type || ""}</strong> (${x.client_id || "n/a"})`
      });
    }
    for (const x of anniversaries.items || []) {
      events.push({
        sort: timelineSortKey(x.trigger_date),
        line: `${x.trigger_date || "?"} — Anniversary <strong>${x.trigger_type || ""}</strong> (${x.client_id || "n/a"})`
      });
    }
    for (const x of taxCp.items || []) {
      events.push({
        sort: timelineSortKey(x.checkpoint_date),
        line: `${x.checkpoint_date || "?"} — Tax checkpoint <strong>${x.checkpoint_type || ""}</strong> (${x.client_id || "n/a"}) [${x.status || ""}]`
      });
    }
    events.sort((a, b) => a.sort.localeCompare(b.sort));
    const top = events.slice(0, 25);
    const tl = panel.querySelector("#dash-timeline");
    tl.innerHTML = top.map((e) => `<li>${e.line}</li>`).join("");

    jsonOutput.textContent = JSON.stringify({ metrics, timeline_sample: top.length, importantDates, anniversaries, taxCp }, null, 2);
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
    panel.querySelector(".record-list").innerHTML = (jobs.items || [])
      .map((j) => `<li>${j.job_type} - ${j.status} (${j.created_at || "n/a"})</li>`)
      .join("");

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

  function addDaysIso(days) {
    const d = new Date();
    d.setDate(d.getDate() + days);
    return d.toISOString().slice(0, 10);
  }

  async function renderObjectTab(panel, tab, jsonOutput) {
    const form = panel.querySelector(".object-form");
    const submitBtn = panel.querySelector(".submit-btn");
    submitBtn.form = "";
    form.innerHTML = "";

    panel.querySelectorAll(".quick-actions").forEach((el) => el.remove());

    if (tab.readonly || !tab.fields?.length) {
      form.innerHTML = '<p class="muted small">Read-only view for this tab.</p>';
      submitBtn.style.display = "none";
    } else {
      submitBtn.style.display = "inline-block";
      if (tab.quickActions) {
        const qa = document.createElement("div");
        qa.className = "quick-actions";
        qa.innerHTML = `
          <h4>Quick actions</h4>
          <p class="muted small">Click a client row to set the client id, then create a task or load cross-product recommendations.</p>
          <div class="qa-row">
            <label for="qa-client-id">Client ID</label>
            <input id="qa-client-id" type="text" placeholder="e.g. C-FIX-RENEWAL" />
            <button type="button" class="submit-btn" id="qa-task">Create follow-up task</button>
            <button type="button" class="submit-btn secondary" id="qa-recs">Load recommendations</button>
          </div>
          <pre class="qa-out muted small" id="qa-out"></pre>
        `;
        form.insertAdjacentElement("beforebegin", qa);
        const outEl = qa.querySelector("#qa-out");
        qa.querySelector("#qa-task").addEventListener("click", async () => {
          const clientId = qa.querySelector("#qa-client-id").value.trim();
          if (!clientId) {
            outEl.textContent = "Set a client id first.";
            return;
          }
          try {
            const body = {
              client_id: clientId,
              task_type: "follow_up",
              status: "pending",
              due_date: addDaysIso(7)
            };
            const r = await callJson("/v1/tasks", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(body)
            });
            outEl.textContent = JSON.stringify(r, null, 2);
          } catch (e) {
            outEl.textContent = String(e);
          }
        });
        qa.querySelector("#qa-recs").addEventListener("click", async () => {
          const clientId = qa.querySelector("#qa-client-id").value.trim();
          if (!clientId) {
            outEl.textContent = "Set a client id first.";
            return;
          }
          try {
            const r = await callJson("/v1/recommendations?limit=500");
            const mine = (r.items || []).filter((i) => i.client_id === clientId);
            outEl.textContent = JSON.stringify({ client_id: clientId, count: mine.length, items: mine }, null, 2);
          } catch (e) {
            outEl.textContent = String(e);
          }
        });
      }
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
    const ul = panel.querySelector(".record-list");
    ul.innerHTML = (response.items || [])
      .map((x) => {
        const title = x.id || x.client_id || x.household_name || "record";
        const idAttr = x.id ? ` data-id="${String(x.id).replace(/"/g, "")}"` : "";
        return `<li${idAttr} class="record-li"><strong>${title}</strong><br/>${Object.entries(x)
          .slice(0, 4)
          .map(([k, v]) => `${k}: ${String(v)}`)
          .join(" | ")}</li>`;
      })
      .join("");

    if (tab.quickActions) {
      const qa = panel.querySelector(".quick-actions");
      const input = qa?.querySelector("#qa-client-id");
      ul.querySelectorAll(".record-li[data-id]").forEach((li) => {
        li.style.cursor = "pointer";
        li.addEventListener("click", () => {
          if (input) input.value = li.getAttribute("data-id") || "";
        });
      });
    }

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
