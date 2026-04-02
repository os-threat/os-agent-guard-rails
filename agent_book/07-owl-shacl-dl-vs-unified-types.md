# OWL, SHACL, Description Logics vs. unified types (book ch. 11–12 / 13–14)

## OWL’s useful core

OWL = classes, object/datatype properties, individuals; **TBox** (terminology) vs **ABox** (facts); reasoning in **Description Logics** (trade expressiveness for decidability).

## Operational pain called out in the book

1. **Ontology split from store** — OWL files + triple store + mapping logic; drift and inconsistency between **asserted** data and **intended** ontology.

2. **OWA** — absence ≠ false; fine for the open web, awkward for **“is this shipment allowed now?”** style automation unless you pile on explicit negatives.

3. **Reasoner cost** — large ABox + DL reasoning can become a bottleneck; production systems sometimes **disable** reasoning and treat OWL as documentation.

4. **Verbosity** — RDF/XML/Turtle ceremony vs. maintaining operational schemas.

## SHACL: second system problem

SHACL adds **shapes** (node/property constraints; can embed SPARQL). The book’s **Beyond OWL** chapter stresses: **OWL reasoner ≠ SHACL validator**—they do not share one proof system; inferred triples may not automatically re-trigger shape validation unless orchestrated.

**Guardrail angle:** duplicating “employee must have exactly one manager” in **both** OWL and SHACL is **fragile**. TypeDB’s direction is **one** type system where **structure + validation** live together.

## DL expressiveness ceiling (examples from the book)

OWL/DL struggles with typical **operational** constraints, e.g.:

- **Dependent** constraints (manager clearance ≥ employee level keyed off another field).
- **Workflow** constraints (“if X manages Y and Y manages Z, transition needs director approval”).
- **Proof-relevant** constraints (claim valid only with **evidence of type T**).

Those tend to leak into **application code**—opaque to agents.

## Dependent types as unification (conceptual)

The book maps:

- OWL subclass → `sub`
- Object property → **relation + roles**
- Datatype property → **attribute**
- Restrictions/cardinality → role constraints, cardinality annotations, functions
- DL inference → **functions** / composable queries

**SHACL node shape** ≈ **record-like** type with fields; **closed shape** ≈ no extra properties at type level—conceptually “one system” rather than validator + ontology.

## What we still do in practice

Even with TypeDB, **business rules** your users type in English still need **elicitation, versioning, and UI**—the book does not remove that. The win is **storage + query + enforcement** in **one** language (TypeQL) for the **shadow** layer, with **MCP** exposing **stable** check entry points.

## Takeaway

For **OpenClaw guard rails**, prefer **TypeQL types + functions** as the **single** truth for “what may exist” and “what follows from data,” and avoid reintroducing a **parallel** SHACL-like validator unless you have a **hard** requirement for RDF interchange—in which case treat mapping as an **export**, not the live guard path.
