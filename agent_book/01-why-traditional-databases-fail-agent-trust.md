# Why typical databases do not satisfy agent “meta-queries” or complete trust

## The gap the book names

Agents need **perception, reasoning, and memory**. Industry optimized the first two; **memory** is still the weak link when “memory” must mean *knowledge with structure and enforceable rules*, not just retrieval of similar text.

The book contrasts:

- **Vector stores**: similarity is not knowledge. They cannot reliably answer *why*, *what caused*, or *how facts relate structurally*. Example in the memory chapter: opposite sentiments can embed too close together—meaning collapses.

- **Property graphs (e.g. Cypher)**: edges are **binary**; n-ary facts are **reified** into fake nodes. The DB does not treat the hyperedge as one semantic unit, so **joint constraints on all participants** are easy to lose or encode only in application code.

- **RDF / OWL-style openness**: almost anything can be asserted about anything. **Contradictions can sit in the store**; constraints often live in a **separate** reasoning layer rather than refusing bad data at the data model boundary.

- **Relational SQL**: strong for transactions and CWA-style absence-as-negation within a table, but **object–model impedance mismatch** is systemic: junction tables for n-ary facts, **roles and domain meaning** carried only by naming convention, **subtype hierarchies** simulated with nullable columns or extra joins, and **business rules** scattered across apps—not introspectable as a single ontology.

- **Document DBs**: flexibility invites **schema drift**; references are not enforced like FKs; **constraints are invisible** to an agent unless duplicated in code. For autonomous automation, silent structural variance is dangerous.

## What agents need that these stacks under-provide

From the “agents need ontologies” chapter, distilled:

1. **Explicit** rules of the domain—not only buried in validators and docs.

2. **Queryable** rules—the agent (or tooling) can ask what types, roles, and constraints exist, not guess from samples.

3. **Enforceable** rules—violation should be **impossible at the persistence layer** for structural/typed constraints, not “best effort” in each microservice.

4. **Introspectable** rules—absence of a relationship in the schema is a **clear signal**; empty query results mean something definable (under CWA), not “unknown vs. unsupported” confusion.

## Meta-queries beyond content

“Meta-queries” in the sense of this project include:

- What **entity and relation types** exist, and which **roles** each relation requires?

- For a proposed action (e.g. post invoice, reassign order), what **preconditions** are stated in the ontology or derived **functions**?

- What **attributes** are legal on which types, and with what **value types**?

Relational and document systems expose **catalogs** and **JSON shapes**, but not a **unified, typed ontology** where relations are first-class, n-ary, and **composable** (relations about relations). Graph stores expose labels and properties but often lack **hard** typing and **dependent** constraints across participants.

## Trust vs. “having read the data”

The book’s Russell / Curry–Howard thread: **unconstrained assertion ⇒ semantic chaos**; **types as propositions** ⇒ many invalid states **cannot be written**. Trust for automation is not “the LLM saw a row once” but “the **combined** schema + data + queries **cannot** represent a forbidden transition without failing fast.”

Traditional operational DBs are usually **authoritative for rows** but **not** for a machine-navigable, enforceable **theory** of allowed actions—hence they are **content** for the agent, not a **complete guardrail substrate**.

## Takeaway for guard rails

For RPA-style agents, a raw SQL or document API is **necessary** for reads/writes but **insufficient** for:

- discovering **all** relevant constraints before acting,

- expressing **multi-party** business facts as single typed assertions,

- turning policy into **checkable queries** with stable semantics.

That is the niche the book assigns to a **typed knowledge layer** (TypeDB), not to the legacy store alone.
