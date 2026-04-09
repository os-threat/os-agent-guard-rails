# Financial services scenario — Investor demo scripts

**Audience:** Local run on Windows + Docker Desktop (Linux containers), iframe UI in OpenClaw.

This demo script reflects the expanded scope: investments, savings, super, insurance, anniversaries, and communication intelligence.

---

## Quick reference

### Core rules to highlight

- Planning: FP-R01, FP-R02, FP-R03
- Insurance/super: FP-R06..FP-R12
- Engagement/social/contact: FP-R13..FP-R17
- Tax and audit: FP-R18..FP-R21

### Core tasks to show

- F1 Client 360 review
- F2 Insurance renewal campaign
- F4 Tax pre-window trigger
- F5 Social engagement personalization
- F6 Complaint-safe communication
- F8 Audit replay

---

## 1-minute demo

**Goal:** Show this is not just investment planning.

1. Open dashboard with upcoming anniversaries and outreach queue.
2. Open one client with mixed products (investment + super + insurance).
3. Trigger insurance-anniversary action (F2) and show auto-generated outreach task.
4. Show rule hit (`FP-R09` + `FP-R13`) and `trace_id`.

**Close line:** Guardrails turn client data into better timing and communication, not just better portfolio math.

---

## 5-minute demo

**Goal:** Show breadth + sophistication.

| Minute | Step |
|--------|------|
| 0:00-0:45 | Architecture one-liner: OpenAPI -> shadow TypeDB -> rules -> promise graph. |
| 0:45-1:30 | UI tabs: Dashboard, Admin, Clients, Super, Insurance, Communications, Tasks. |
| 1:30-2:30 | F1 Client 360 run: cross-product action list. |
| 2:30-3:30 | F2 Insurance renewal + anniversary outreach with channel consent rule. |
| 3:30-4:20 | F4 Tax 1-month trigger and escalation path. |
| 4:20-5:00 | F8 replay audit with `trace_id` and promise outcome. |

---

## 20-minute demo

**Goal:** Full operating model and enterprise credibility.

### Block 1 (0-4 min): Problem and scope

- Financial advice operations are multi-product, time-sensitive, communication-heavy.
- Traditional automation misses timing, consent, and context.

### Block 2 (4-8 min): Product walkthrough

- Show sophisticated tabbed iframe UI
- Show form-first object pages (not JSON-first)
- Show Admin page (jobs, data health, replay controls)

### Block 3 (8-13 min): Rule management story

- Walk through rule families:
  - planning and suitability
  - insurance and super obligations
  - engagement/social/contact intelligence
  - tax-window timing and audit rules

### Block 4 (13-17 min): Live task sequence

1. F1 Client 360
2. F2 Insurance-anniversary campaign
3. F5 Social personalization
4. F6 Complaint-safe block
5. F4 Tax trigger

### Block 5 (17-20 min): Assurance and operations

- F8 replay validation
- Promise and guard dashboards
- Exception handling and overrides
- Deployment model: Windows dev, Docker Desktop runtime, localhost iframe integration

---

## Backup demo assets

- pre-recorded F4 run showing tax window trigger
- pre-recorded F6 block showing outreach suppression
- static screenshots of admin replay and audit trace detail
