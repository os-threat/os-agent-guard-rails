# Financial services scenario — Using OS-Agent RPA Guard Rails

**Companion:** [`PLAN.md`](PLAN.md), [`DEMO.md`](DEMO.md)

This is the operational manual for Scenario 2 after scope expansion. It covers:
- OpenAPI registration
- cross-product rule authoring
- task definitions (including extraction scope)
- execution and evaluation

---

## 0. Actors

- **Advisor user**: configures rules, tasks, and approvals
- **OpenClaw agent**: executes UI/API workflows
- **Operations reviewer**: handles escalations and overrides

---

## 1. Register API and initialize shadow schema

1. Start stack with Docker Desktop (`docker compose up --build`).
2. In plugin UI: Register OpenAPI service.
3. Use spec URL and base URL from scenario app.
4. Plugin transpiles OpenAPI into Layer A TypeDB schema.
5. Confirm entities include clients, products, insurance, super, communications, campaigns, anniversaries, and tasks.

---

## 2. Rule set (enhanced, cross-product)

Create one rule set, e.g. `financial-services-v2-default`.

### A. Portfolio / planning rules

- **FP-R01** Diversification threshold by risk tier
- **FP-R02** Product suitability by risk + horizon
- **FP-R03** Goal horizon mismatch detection

### B. Savings / cashflow rules

- **FP-R04** Emergency fund below target triggers contact
- **FP-R05** Short-term savings milestone drift task

### C. Superannuation rules

- **FP-R06** Contribution cap warning and escalation
- **FP-R07** Missing beneficiary review reminder
- **FP-R08** Insurance-inside-super adequacy check

### D. Insurance rules

- **FP-R09** Policy renewal due in 30 days creates outreach
- **FP-R10** Household insurance coverage gap alert
- **FP-R11** Business insurance review cadence enforcement
- **FP-R12** Death/life cover mismatch to dependent profile

### E. Engagement / communication / social rules

- **FP-R13** Preferred channel and consent enforcement
- **FP-R14** No promotional contact during unresolved complaint window
- **FP-R15** Social media task only for opted-in segment
- **FP-R16** Contact-frequency fatigue prevention
- **FP-R17** Anniversary outreach personalization rule

### F. Tax timing rules

- **FP-R18** Tax planning workflow exactly 1 month before due window
- **FP-R19** Escalate missing tax response after X days

### G. Platform and audit rules

- **FP-R20** Every denial or failure includes `trace_id`
- **FP-R21** Idempotency required for mutating workflow endpoints

---

## 3. Task definitions (data import is task-driven)

Each task must explicitly define extraction scope (which endpoints, fields, and joins are loaded into Layer A).

### F1 — Client 360 review task

- Pull client profile, household, products, anniversaries, communication history
- Outcome: prioritized advisor action list

### F2 — Insurance renewal campaign

- Find policies with 30-day anniversary windows
- Generate outreach tasks and communication drafts
- Rules: FP-R09, FP-R13, FP-R17

### F3 — Super health check

- Evaluate contribution caps, beneficiaries, and insurance in super
- Rules: FP-R06, FP-R07, FP-R08

### F4 — Tax planning pre-window task

- Trigger exactly 1 month prior
- Build contact queue and escalation actions
- Rules: FP-R18, FP-R19, FP-R13

### F5 — Social engagement personalization

- Build opted-in audience segments
- Create campaign + contact tasks by profile and anniversaries
- Rules: FP-R15, FP-R16, FP-R17

### F6 — Complaint-safe communications

- Block or reroute outreach if unresolved complaints exist
- Rules: FP-R14, FP-R13

### F7 — Portfolio + savings mixed recommendation

- Combined investment + savings adjustment recommendation
- Rules: FP-R01..FP-R05

### F8 — Audit and replay validation

- Re-run selected tasks in dry-run mode
- Verify `trace_id`, decisions, promise links
- Rules: FP-R20, FP-R21

---

## 4. Execution workflow

1. Select task template (F1..F8)
2. Confirm extraction scope and parameters
3. Run task via agent
4. Evaluate ALLOW/DENY or action generation results
5. Apply override path where required
6. Record promise outcomes in Layer B

---

## 5. Evaluation metrics

### Guard effectiveness
- rule hit counts by rule id
- deny/allow ratio by task type
- escalation rate

### Engagement quality
- contact success by channel
- opt-in vs opt-out compliance
- campaign response rates

### Operational quality
- overdue tasks
- anniversary task completion SLA
- tax-window completion SLA

### Audit quality
- `trace_id` completeness
- replay consistency
- override reason quality

---

## 6. Artifact expectations for demo/readout

Produce at least:
1. one successful cross-product client review (F1)
2. one insurance-anniversary triggered campaign run (F2)
3. one tax-window trigger run (F4)
4. one complaint-safe communication block (F6)
5. one full audit replay with trace links (F8)
