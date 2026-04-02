# PERA and polymorphism (book ch. 6–7) → guardrail modeling

## PERA in one line

**Polymorphic Entity–Relation–Attribute**: three first-class kinds—**entities** (things that can exist on their own), **relations** (typed hyperedges with **named roles** and their own attributes), **attributes** (typed values, **decoupled** from a single table—same attribute type can be owned by multiple entity/relation types).

## Why this matters for a SQL shadow

Operational SQL maps awkwardly to “one real-world n-ary fact”:

- Junction tables hide **role semantics** (IDs are not roles).
- Subtype modeling uses **STI/CTI/Concrete Table** hacks—nullable columns, `UNION ALL`, or duplicated columns—so **invariants** drift into app code.

In PERA, a guardrail schema can mirror **business events** as single relation instances (e.g. `transfer` with `payer`, `payee`, `account`, `amount`, …) so **one query** asks “is this whole configuration legal?” instead of stitching six joins the agent must get right every time.

## Relations vs. property-graph edges

The book’s contrast: property-graph edges are **binary** and **second-class**; n-ary facts need **reified** hub nodes. In TypeDB, the relation is a **first-class typed value**: it can **own attributes** and **play roles in other relations** (foundation for metagraphs—see [10-structures-memory-time-coordination.md](10-structures-memory-time-coordination.md)).

**Guardrail use:** attach **evidence**, **severity**, **rule-id**, or **evaluated-at** on the **relation** that represents the automation checkpoint, not only on endpoints.

## Shared attributes

Because attribute **types** can be owned by several entity types (e.g. `confidence-score` on `person`, `ai-model`, and `prediction`), you can express **cross-cutting** policies (“trust only if …”) with **one attribute semantics** instead of duplicating column names across tables.

## Three polymorphisms (ch. 7)

1. **Inheritance polymorphism** — `sub` on entities, relations, and **attributes**. Queries against a supertype include subtypes **without** `UNION`/`JOIN` explosion.

2. **Interface polymorphism** — unrelated types play the **same role** (e.g. `company`, `nonprofit`, `government-agency` all `employment:employer`). Policies can be written against **roles**, not each concrete table.

3. **Parametric polymorphism** — type variables in queries (see [05-typeql-programmability-and-mcp.md](05-typeql-programmability-and-mcp.md)): generic “what plays role R?” introspection for **dynamic** MCP tool discovery.

## Practical guardrail takeaway

When transpiling SQL → TQL:

- Prefer **entities** for row types, **attributes** for columns with clear value types, **relations** for FK webs that represent **one** business fact with **roles**.

- Use **`sub`** for real subtyping (customers, accounts, order types) so **one** function `applies_to($x: order)` can cover future subtypes if you query at the supertype.

- Encode **forbidden role players** by **not** declaring `plays`—enforcement is **structural**, not a string check in the agent prompt.
