# “Queries as types” and explainability (book ch. 8b / type-theory chapter)

## Unifying lens

The book argues **type theory** subsumes relational, document, and graph models as **special cases**:

- Relational ≈ flat entities, binary relations, no inheritance.
- Document ≈ nested structs/lists on entities, weak cross-links.
- Property graph ≈ entities + binary relations + properties.

TypeDB adds **inheritance, n-ary relations, interface polymorphism, parametric polymorphism, dependent constraints, inference**—needed for rich guardrails, not just “another graph.”

## Queries as types (propositions as types, operationalized)

The manuscript cites the TypeQL line: a **`match` constructs a type**; **results are inhabitants** (proofs). Empty result = **no proof** (under CWA-style reading in the operational layer).

**Guardrail implications:**

1. **Explainability** — a positive result is backed by a **witness chain** (variable bindings satisfying each constraint). Surfacing those bindings in MCP responses gives **auditable** “why allowed/denied” without only returning a boolean.

2. **Composability** — sub-queries / functions compose when **types align**; the engine rejects meaningless composition **early** (resolver as **type checker**).

3. **Agent safety** — the LLM is less likely to “query nonsense” if the driver validates queries: wrong roles or attribute types fail **before** touching data.

## Formal references (from the book)

Useful for internal design docs or citations:

- *TypeQL: A Type-Theoretic & Polymorphic Query Language* — ACM SIGMOD/PODS 2024 (Best Newcomer Award), cited as formalizing TypeQL in dependent type theory.
- *Type Theory as a Unifying Paradigm for Modern Databases* — mathematical treatment of PERA + unification of paradigms.

## Practical takeaway for os-agent-guard-rails

Treat each guardrail check as:

- a **typed proposition** (“this `order` may transition to `posted`”), and

- MCP returns **proof-carrying** data (matched entities, rule ids, key attribute values)—not just `ok: true`.

This aligns with **RPA audit** requirements and reduces **silent** failures when the agent misinterprets an empty result.
