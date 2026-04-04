# Financial planner API scenario — Using OS-Agent RPA Guard Rails

**Companion:** [`PLAN.md`](PLAN.md), [`DEMO.md`](DEMO.md).  
**Prereqs:** Mock API + MongoDB on localhost, full Swagger UI, plugin **Stage 2**, TypeDB for shadow + promise graph.

This document is a **step-by-step manual**: you add the **exact rules** and **exact tasks** below into the plugin/skill UI. **Shadow data import is driven by tasks:** defining a task specifies **which API responses** (which GETs/POSTs and fields) are extracted and materialized into TypeDB Layer A. There is **no** standalone “sync everything” step before tasks unless the product later adds an optional global sync—the **authoritative** extract for demos is **per task definition**.

---

## 0. Actors

- **User** — registers the API, enters rules, defines tasks (including extract scope), runs and reviews.  
- **OpenClaw agent** — HTTP or browser automation against the mini-app / API.  
- **Compliance reviewer** — optional human node in the promise graph for escalations.

---

## 1. Register the API and materialize the shadow schema

1. Start the stack: `docker compose up` (or `npm start`) so **MongoDB**, mock server, and **Swagger UI** (e.g. `http://localhost:8082/docs`) are up.  
2. In **OS-Agent Guard Rails** → **Register** → **OpenAPI / REST**.  
3. Point at the **full** spec: `financial-planner.yaml` and/or `http://localhost:8082/v1` base URL (per **PLAN.md**).  
4. **Background:** plugin parses OpenAPI → **TypeQL `define`** for Layer A (schema only, no business data yet).  
5. Optionally configure **TypeQL import templates** per operation (how JSON maps into shadow entities)—these will be **invoked when tasks run** according to each task’s extract definition.

**Success criteria:** Registration green; **TypeQL viewer** lists HTTP-oriented and domain types; Swagger shows every route documented.

---

## 2. Add the rule set (exact list)

Create **one rule set** (e.g. `financial-planner-default-v1`) and add **these twelve rules** in order. For each, use the **Rule composer** (natural language left; Logic + TypeQL viewers right). Use the **Rule ID** when talking to support or demos.

| ID | Rule name (short) | Natural language (paste or paraphrase) | Guard MCP tool name (suggested) |
|----|-------------------|----------------------------------------|-----------------------------------|
| **FP-R01** | Single-name concentration | If the client’s risk tier is **moderate** or **conservative**, deny any recommendation or trade that would leave a single equity position above **15%** of total account value for that account. | `fp_concentration_single_equity` |
| **FP-R02** | Risk tier vs asset mix | If the proposed recommendation’s dominant asset class is **not** allowed for the client’s **risk_tier** (per product matrix in rule appendix), deny. | `fp_risk_tier_asset_mix` |
| **FP-R03** | KYC / product gate | If the product or symbol requires **accredited** (or higher **kyc_tier**) and the client does not meet it, deny. | `fp_kyc_product_gate` |
| **FP-R04** | Fee disclosure before trade | Deny **trade execute** if there is no **accepted** fee/disclosure record for that **account** within policy window (e.g. 90 days) when the trade would incur a fee. | `fp_fee_disclosure_accepted` |
| **FP-R05** | Preview before execute | Deny **trade execute** (`preview: false` or equivalent) if there is no successful **preview** for the same account + symbol intent in the same session (or linked **preview_id** per your API design). | `fp_preview_before_execute` |
| **FP-R06** | Idempotency on mutating POST | Deny `POST /recommendations` or `POST /trades` if the **Idempotency-Key** header is missing or malformed. | `fp_idempotency_required` |
| **FP-R07** | Wash-sale window | Deny a **buy** if the same **symbol** had a **loss sale** in the same account within the configured **wash-sale window** (e.g. 30 days) before this buy. | `fp_wash_sale_window` |
| **FP-R08** | IRA vs taxable instruments | Deny holdings or trades that violate account type: e.g. **margin-only** or **restricted** instruments in **IRA** accounts. | `fp_ira_account_constraints` |
| **FP-R09** | Goal horizon vs portfolio | If a **goal** linked to the plan has **target_date** within **5 years**, deny recommendations that push the portfolio into **long-duration-only** stance incompatible with that horizon (per rule thresholds). | `fp_goal_horizon_match` |
| **FP-R10** | Problem Details trace_id | Any **4xx/5xx** from the API must carry **`trace_id`**; the guard layer must persist that id on the **assessment** / **data-trace** link for audit. | `fp_trace_id_logged` |
| **FP-R11** | Daily trade frequency cap | Deny if the client would exceed **N** executed trades per **rolling business day** (e.g. N=20 for demo). | `fp_daily_trade_cap` |
| **FP-R12** | Sector concentration | If **moderate** risk, deny if any single **GICS sector** (or tagged sector) exceeds **40%** of account value after the proposed change. | `fp_sector_concentration` |

**Success criteria:** All **FP-R01**–**FP-R12** appear in the rule list; **`fun`** appended to schema; **no** shadow business data required yet for rules to exist.

---

## 3. Define RPA tasks (each task defines extraction into TypeDB)

For **each** task below, in **Tasks** → **New task**, set **name**, **parameters**, **OpenClaw agent** profile, and the **data extraction definition**: which operations to call (or which UI steps imply those calls) and which JSON paths populate which shadow entities. That definition is what the plugin uses to **import** into Layer A for that task run.

### Task F1 — “Recommendation — ALLOW path (well-diversified client)”

- **Goal:** Show **ALLOW** on `POST /recommendations` for client **`C-ALLOW`** (seed id from **PLAN**).  
- **Parameters:** `client_id=C-ALLOW`, horizon years, `Idempotency-Key` UUID.  
- **Extract for shadow (minimum):** `GET /clients/{id}`, `GET /accounts?client_id=…`, `GET /accounts/{id}/holdings` for each account, `GET /plans`, `GET /plans/{id}/goals` if needed for FP-R09.  
- **Guard hooks before POST:** FP-R01, FP-R02, FP-R06, FP-R09 (others as applicable).  
- **Promise hooks:** create session + shared-task + promise chain for “recommendation cycle.”

### Task F2 — “Recommendation — DENY path (concentration breach)”

- **Goal:** Show **DENY** for client **`C-DENY`** seeded with **>15%** single equity (FP-R01) or sector breach (FP-R12).  
- **Parameters:** `client_id=C-DENY`.  
- **Extract:** same as F1 for that client.  
- **Guard hooks:** FP-R01, FP-R12, FP-R02.  
- **Expected:** HTTP **403/422** or plugin-level DENY with **witness** (symbol, %).

### Task F3 — “Trade — preview then execute (disclosure + preview order)”

- **Goal:** Exercise FP-R04, FP-R05, FP-R06, FP-R07, FP-R08, FP-R11.  
- **Steps:** `POST /trades` with **preview**; accept disclosure via `POST /documents` if required; then execute.  
- **Extract:** client, account, holdings, fee schedules, disclosure records, trade preview audit collection.  
- **Guard hooks:** FP-R04, FP-R05, FP-R06, FP-R07, FP-R08, FP-R11.

### Task F4 — “KYC gate — restricted product”

- **Goal:** FP-R03 **DENY** — attempt recommendation or trade for **`C-NON-ACC`** into **accredited-only** symbol (seed).  
- **Extract:** `GET /clients/{id}` + product metadata from recommendation response or static catalog in shadow.  
- **Guard hooks:** FP-R03.

### Task F5 — “Error path — trace_id on assessment”

- **Goal:** FP-R10 — force a **4xx** with `trace_id`; confirm promise **assessment** stores it.  
- **Extract:** minimal; error payload only.  
- **Guard hooks:** FP-R10.

---

## 4. Import shadow data (per task run)

When you **run** a task (or dry-run extract):

1. The plugin executes the **extract** you attached to that task (GETs / staged POSTs as defined).  
2. **Background:** JSON → **TypeQL insert/put** into Layer A for the **scope** of that task.  
3. UI shows **extract timestamp**, **document/row counts**, and any **UNKNOWN** fields if the API did not return needed facts.

**Important:** This replaces a vague “sync everything first” flow: **task F1** brings in what F1 needs; **F3** may pull a **superset** including fees and disclosures. Re-running a task refreshes that slice.

---

## 5. Schedule and run

1. Schedule **F1** or run ad hoc; observe **ALLOW** and promise **fulfilled**.  
2. Run **F2**; observe **DENY** + **witness**.  
3. Run **F3**–**F5** as needed for breadth.  
4. **Override path:** user approves exception → **decision** + **assessment** on promise graph.

---

## 6. Evaluate

1. **Task dashboard** — per-task success, latency, ALLOW/DENY counts.  
2. **Promise statistics** — fulfillment vs broken; link **trace_id** (FP-R10).  
3. **Guard effectiveness** — counts by **FP-Rxx** rule id.

---

## 7. Artifacts for investor

- One **ALLOW** log (F1); one **DENY** log (F2) with witness; one **promise** triple with **trace_id** (F5).
