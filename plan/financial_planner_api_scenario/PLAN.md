# Financial services platform mini-app — Build plan (`plan/financial_planner_api_scenario`)

**Purpose:** Build a richer Scenario 2 mini-app: a Swagger/OpenAPI-first REST platform for advisory operations across **investments, short-term savings, superannuation, and insurance** (general, household, death/life, business), with anniversaries and lifecycle triggers.

**Stage split:**
- **Stage 1:** this document set (`PLAN.md`, `SCENARIO.md`, `DEMO.md`)
- **Stage 2:** implementation in `code/financial_planner_api_scenario`

**Runtime model:** development on **Windows**, default startup on **Docker Desktop** (Linux containers, optional WSL shell). UI must be iframe-friendly for OpenClaw embedding.

---

## 1. Scope (v2)

This scenario is no longer just portfolio planning. It models a multi-line advisory business:

1. Wealth/investments and goals
2. Short-term savings products and emergency funds
3. Superannuation (contributions, beneficiaries, insurance in super)
4. Insurance portfolio:
   - General insurance
   - Household/home insurance
   - Death/life insurance
   - Business insurance
5. Client communications, social engagement tasks, and contact cadence
6. Anniversary and event-driven actions (renewals, birthdays, tax milestones, review anniversaries)

---

## 2. Repository layout (Stage 2 target)

```text
code/financial_planner_api_scenario/
  openapi/
    financial-services.yaml
  api/
    server.js
    package.json
    src/
      routes/
      services/
      rules/
      ui/
  db/
    mongo-init/
  seed/
    generate_data.py or generate_data.js
  docker-compose.yml
  tests/
    test_contract.sh
    test_rules.spec.ts
    test_e2e.spec.ts
plan/financial_planner_api_scenario/
  PLAN.md
  SCENARIO.md
  DEMO.md
```

---

## 3. API design (OpenAPI single source of truth)

**Base path:** `/v1`

### 3.1 Core domain resources

- `/clients`, `/clients/{id}`
- `/households`, `/households/{id}`
- `/addresses`
- `/profiles` (risk, preferences, communication consent)
- `/important-dates` (birthdays, policy anniversaries, review anniversaries, tax milestones)

### 3.2 Product resources

- `/investment-accounts`, `/investment-holdings`
- `/savings-accounts`
- `/super-accounts`, `/super-contributions`, `/super-beneficiaries`
- `/insurance-policies`, `/insurance-coverages`, `/insurance-renewals`, `/insurance-claims`

### 3.3 Workflow resources

- `/recommendations` (cross-product)
- `/tasks` (contact, outreach, follow-up, review booking)
- `/communications` (email/sms/call logs, status)
- `/campaigns` (social/post cadence + audience segments)
- `/anniversary-triggers`
- `/tax-planning-checkpoints`

### 3.4 Platform resources

- `/admin/health`
- `/admin/jobs` (seed/reindex/replay)
- `/admin/audit`
- `/dashboard/metrics`

### 3.5 Contract requirements

Every operation must include:
- summary + description
- tags
- parameters
- requestBody schemas
- response schemas
- realistic examples
- error model: `application/problem+json` with `trace_id`

---

## 4. Data model and richness targets

Use realistic, fully human data with rich relational links.

### 4.1 Client identity

Each client record includes:
- first name, last name
- date of birth
- full address + region/state/postcode
- household links (partner, dependents, business role)
- communication channel preferences + consent

### 4.2 Product richness

Each client has a mixed product portfolio (not all clients have all products):
- investment plan + holdings
- short-term savings objective
- super accounts (possibly multiple)
- 1..N insurance policies across the four categories
- policy renewal terms and anniversaries

### 4.3 Event richness

Important dates drive actions:
- birthday
- review anniversary
- policy anniversary/renewal
- contribution deadlines
- 1-month pre-tax-planning window

### 4.4 Suggested seed volumes

- `clients`: 350-600
- `households`: 150-250
- `important_dates`: 2,000+
- `investment_accounts`: 300-500
- `savings_accounts`: 250-450
- `super_accounts`: 300-500
- `insurance_policies`: 600-1,200
- `communications`: 5,000+
- `tasks`: 3,000+
- `anniversary_triggers`: 2,000+

---

## 5. UI requirements (iframe-first, sophisticated)

The web UI must be tab-driven, object-focused, and form-centric. JSON is a secondary diagnostics view only.

### Required pages

1. `Dashboard`
2. `Admin`
3. `Clients`
4. `Households`
5. `Investments`
6. `Savings`
7. `Superannuation`
8. `Insurance`
9. `Communications`
10. `Campaigns`
11. `Tasks & Triggers`
12. `Audit/Activity`

**Minimum object screens:** at least six object-specific screens are mandatory; this plan defines ten.

### UX expectations

- list + detail + create/edit form per object tab
- linked quick actions (create task, schedule communication, generate review)
- timeline panel for anniversaries and upcoming obligations
- JSON inspector as secondary right drawer or debug tab

---

## 6. Rules strategy (cross-product + engagement)

Rules are not only investment suitability. They must combine:

1. financial suitability and compliance
2. insurance and super coverage logic
3. timing logic (tax and anniversaries)
4. contact strategy and social engagement quality
5. client-sensitive communication behavior
6. social media campaign targetted at anniversaries

Examples:
- renewal reminder cadence based on policy type
- no promotional outreach if recent complaint unresolved
- tax-planning outreach exactly 30-day window with fallback escalation
- anniversary-generated review tasks with household-aware bundling
- social media campaign targetted at anniversaries

(Full operational list in `SCENARIO.md`.)

---

## 7. Docker Desktop-first operations

Default startup path:

1. Open Docker Desktop
2. `docker compose up --build`
3. API + UI + MongoDB on localhost
4. OpenClaw embeds UI in iframe from localhost URL

### Deployment notes

- Development machine: Windows
- Container runtime: Linux containers via Docker Desktop
- Works from PowerShell, cmd, or WSL shell

---

## 8. Testing strategy

1. **Contract tests** against OpenAPI (`financial-services.yaml`)
2. **Rule tests** for all named rules in `SCENARIO.md`
3. **E2E workflows**:
   - investment + savings + insurance + super mixed journeys
   - anniversary-triggered outreach
   - tax-window communication
   - admin rerun/replay
4. **UI tests** for tab navigation, forms, and iframe embedding

---

## 9. Implementation ordering (for issue creation)
Note: Rules engine + workflow orchestration are implemented in the plugin/skill ui, and the api is used to extract the data and materialize it into the shadow schema.

1. Scaffold + Docker + health endpoints
2. OpenAPI contract
3. Core API resources
4. Seed generator + data richness fixtures. 
6. Sophisticated tabbed UI + forms
7. Admin and dashboard pages
8. Full test stack and demo scripts

---

## 10. Disclaimer

All scenario records are fictional. No financial or insurance recommendation in this scenario is real advice.
