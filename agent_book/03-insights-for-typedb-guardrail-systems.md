# Powerful book insights mapped to a TypeDB + MCP guardrail system

Short, actionable distillations from *TypeDB for Edge AI Agents* for this repo (schema shadow, rules, TypeQL functions, SQL extract → TypeQL load, generated MCP).

---

## 1. Types block whole classes of nonsense

**Russell / naive graphs:** unconstrained membership ⇒ paradox; RDF examples show **Person ∧ Organization** or incompatible duplicate properties can **coexist** unless an external reasoner catches them.

**Guardrail use:** encode “what may exist” in TypeDB so **structurally invalid** automation states **never enter** the guard DB. Fail before RPA touches production.

---

## 2. Schema = ontology = safety substrate

The book insists: **schema is not separate decoration**—it is the **machine-readable theory** of the domain. Types are **concepts**; relations with roles are **rules of admissible linkage**; attributes carry **typed** properties.

**Guardrail use:** SQL→TQL transpilation should preserve **entities, keys, and relation arity/roles**, not only tables-as-nodes. Your UI elicits **business rules** on top of that ontology.

---

## 3. Curry–Howard lens: “types as propositions”

A function type is “if inputs, then output”; a well-typed value is a **proof** inhabiting a proposition.

**Guardrail use:** TypeQL **functions** that return `{ boolean }`, sets of violating entities, or required witnesses are **executable propositions**. Exposing them via **MCP tools** gives the agent **checkable** claims instead of prose.

---

## 4. Dependent typing = constraints that reference other facts

Examples: only certain subtypes may play a **role**; validity of a link depends on **other attributes** (e.g. nationality vs destination).

**Guardrail use:** Horn-style **IF** conditions often depend on **multiple tables**—that is dependency in the wild. Encode as match patterns + `not { … }` + functions; keep **single responsibility** per function for composable MCP tools.

---

## 5. Semantic validation of queries

The internals chapter: **ill-typed queries** can be rejected at analysis time (e.g. impossible role combinations).

**Guardrail use:** tooling that generates TypeQL from diagrams should **type-check** early; MCP layer returns **schema errors** as first-class outcomes, not silent empty sets misunderstood as “allowed.”

---

## 6. Polymorphic queries reduce agent fragility

One pattern can span all types owning an attribute or playing a pattern.

**Guardrail use:** generic tools like “list all constraint relations touching type X” support **meta-queries** for agent planning without hard-coding each table name from the source SQL.

---

## 7. Hypergraphs (n-ary relations) without reification

PERA **relations** are **hyperedges** with identity and attributes; **no synthetic junction node** with ambiguous semantics.

**Guardrail use:** model each automation-relevant **business event** (order placed, approval granted, transfer authorized) as one typed relation with roles—easier to attach **rules** and **evidence** uniformly.

---

## 8. Metagraphs: relations about relations

Needed for causality, sequences, and “this decision about that relationship.”

**Guardrail use:** represent **pipeline steps**, **checks**, and **outcomes** so you can query **why** a step was blocked and **what** prior step implied.

---

## 9. Semantic spacetime (Burgess): four primitive edges

**NEAR, CONTAINS, EXPRESSES (property at time), LEADS_TO**—meaning plus **validity/lifecycle**.

**Guardrail use:** time-bounded rules (effective dates, SLA windows) and **causal** explanations for audit. TypeDB models these as **typed relations** rather than ad hoc JSON.

---

## 10. Memory architecture lessons (even if not your primary feature)

RAG ≠ memory; combine **structured** memory with optional **embedding** retrieval; distinguish **episodic** vs **semantic** vs **meta-memory**.

**Guardrail use:** optional for **explaining** denials (“similar past violations”) but **not** a substitute for typed allow/deny. Book warns against **pure** similarity for safety-critical distinctions.

---

## 11. Promise graphs for multi-party automation

Promises, assessments, bilateral trust—useful when tools span **orgs** or **services**.

**Guardrail use:** if OpenClaw invokes **third-party** tools, promise/assessment shapes may model **SLAs and verification**, not just static ACLs.

---

## 12. Open vs closed world: operational closure

TypeDB is framed as **CWA-friendly**: schema defines what **can** exist; absence in a completed query can support **negation-as-failure** *within the shadow KB*.

**Guardrail use:** document **sync scope** so “not in shadow” is not silently treated as “false in enterprise”—only “unknown to guard until imported.”

---

## 13. Honest limits (“what comes next”)

Native **ANN / hybrid** queries, richer collection types, etc. are **partially there or roadmap**.

**Guardrail use:** plan **sidecar** vector search if you need fuzzy document grounding; keep **authoritative** allow/deny on **typed** predicates.

---

## 14. Ontology layer + operational data flow

Book’s diagram: agents should query the ontology **before** acting; writes still go through **operational** channels.

**Guardrail use:** MCP **read-only** checks predominate; mutating production goes through **existing** APIs with the agent having **pre-validated** intent against TypeDB.

---

## 15. Closed schema, open data (pragmatic middle)

The open/closed-world chapter: **schema** is fixed and enforced (**closed**); **instances** can grow freely **within** that schema—new facts without new roles/types. Agents get **predictable** query semantics and extensible data.

**Guardrail use:** ship **migrations** when the business adds new concepts; avoid runtime “anything goes” JSON in the shadow store.

---

## Deeper articles in this folder

| Topic | See |
|--------|-----|
| PERA, three polymorphisms, SQL inheritance hacks | [04-pera-and-polymorphism-for-guardrails.md](04-pera-and-polymorphism-for-guardrails.md) |
| TypeQL statements, `fun`, negation, aggregates, type variables → MCP | [05-typeql-programmability-and-mcp.md](05-typeql-programmability-and-mcp.md) |
| Queries-as-types, explainability, formal papers | [06-queries-as-types-and-explainability.md](06-queries-as-types-and-explainability.md) |
| OWL/SHACL/DL limits vs unified types | [07-owl-shacl-dl-vs-unified-types.md](07-owl-shacl-dl-vs-unified-types.md) |
| KG entropy, inference functions, hybrid vector + graph | [08-knowledge-graphs-entropy-and-hybrid-ai.md](08-knowledge-graphs-entropy-and-hybrid-ai.md) |
| TypeDB 3, Rust, gRPC, `@card`/`@values`, MPL | [09-typedb-3-edge-and-operations.md](09-typedb-3-edge-and-operations.md) |
| Hypergraphs, metagraphs, spacetime, memory, promises | [10-structures-memory-time-coordination.md](10-structures-memory-time-coordination.md) |

Full index: [00-source-and-scope.md](00-source-and-scope.md).

---

## Summary

The manuscript’s through-line for guard rails: **replace “hope the LLM followed the PDF” with “ask typed questions whose answers are structurally bounded.”** Your pipeline (SQL schema → TQL shadow, UI rules → Horn → functions → extract SQL → import TQL → MCP) is the operational spine of that idea for RPA.
