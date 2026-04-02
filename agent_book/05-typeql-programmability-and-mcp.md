# TypeQL programmability (book ch. 8) → MCP guardrail tools

## Core statement shapes

The book emphasizes four pillars: **`define`** (schema as code), **`insert`**, **`match`**, **`delete`**, plus match-driven **updates** (match → delete old facts → insert new). Every write path is **type-checked** against roles and ownership.

**MCP mapping:** separate tools or modes for **schema introspection** (`define` results visible via type queries), **check** (read-only `match`), and **sync** (`insert`/`delete` from ETL)—agents doing RPA checks should usually hold **read-only** credentials on production-adjacent guard DBs.

## Composition = conjunction of constraints

`match` chains **narrow** bindings: each line is a constraint; variables **unify** across lines. This is the declarative equivalent of “join all these preconditions.”

**Guardrail use:** each business rule clause becomes a **pattern fragment**; composed patterns are **AND** semantics—ideal for translating **IF** sides of Horn-style rules.

## Type variables (metaprogramming in queries)

TypeQL allows variables where **types** go (`$entity isa $type`, relations as `$rel`). Agents (or your code generator) can ask:

- What entity types exist?
- What relates type X?
- What attributes appear on instances of Y?

**MCP mapping:** implement **`list_types`**, **`roles_for_relation`**, **`types_playing_role`** as thin wrappers over these patterns so OpenClaw **discovers** the guard surface after each schema generation.

## Functions (`fun`) — primary MCP backend

Book points:

- Schema-level **`fun`** with typed parameters and return types (`boolean`, scalars, or `{ type }` streams).
- **Multiple clauses** for the same function name = **ordered** disjunctive cases (e.g. `age-group`).
- **Recursion** for transitive closure (`knows-transitively`, `can-reach`).
- **Composition** — functions call functions; nest with `let`.
- **Negation** — `not { … }` blocks; stratified negation claimed to keep evaluation sound.

**Guardrail use:** one MCP tool per **named check** you want the agent to call:

- `validate_invoice_posting($invoice_id)` → internally `match` shadow entity, `let` nested `violations($invoice)`, return structured JSON.

Keep **thin** tools: heavy logic stays in **TypeQL functions** so the MCP layer stays generated and auditable.

## Negation as failure (within the shadow KB)

`not { … }` expresses “no proof of this pattern exists.” Under a **closed** shadow with complete **relevant** facts, this matches **guardrail denial** semantics. Document **sync lag**: missing rows mean “unknown to guard,” not necessarily “false in ERP.”

## Aggregates

`reduce`, `count`, `mean`, `max`, grouped aggregates—useful for **limits** (count of open tasks, sum of amounts) in **threshold** rules.

## Semantic query validation

The internals chapter (see also [06-queries-as-types-and-explainability.md](06-queries-as-types-and-explainability.md)): impossible role combinations can be **rejected before execution**. For generated MCP, run **explain/validate** on generated TypeQL in CI so **broken tools** never ship.

## Summary

Your **dynamic MCP server** should mirror **functions + a small set of generic introspection queries**, not arbitrary string SQL. TypeQL gives **composable**, **negation-capable**, **recursive** policy expressions with **compile-time** schema alignment—exactly the surface you want between LLM and automation.
