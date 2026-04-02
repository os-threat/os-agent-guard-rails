# Knowledge graphs, entropy, and hybrid AI (book ch. 12)

## “A KG without ontology is random garbage”

The book’s blunt line: without a **clear ontology** (what types/relations mean, what is legal), graphs accumulate **invalid or nonsensical** facts; inference then **amplifies** error.

**Guardrail mapping:** your **SQL→TQL** step is not just structural migration—it is **ontology commitment**. User-defined rules hang off that ontology; if the shadow schema drifts, **rules silently misfire**.

## Why KGs matter for agents (vs. raw LLM)

- LLMs **confabulate** plausible structure; KGs anchor **entities, roles, and paths**.
- **RAG** quality = retrieval quality; structured retrieval can **traverse** exactly the needed context (e.g. order → supplier → alerts).

## KG vs. vector store (complementary)

- **Vectors:** similarity / fuzzy recall; **lose explicit roles** (“Alice manages project” collapses to a point).
- **KG:** **precise** multi-hop questions with **typed** links.

**Book recommendation:** use **both**—graph for **reasoning and constraints**, vectors for **similarity**; combine in the agent loop.

**Guardrail project:** keep **authoritative allow/deny** on **typed** TypeQL; add **optional** embedding index for **explanations** (“similar past violations”) without letting similarity **override** hard constraints.

## Inference functions as “deductive layer”

Example pattern: derive **responsible-for** deliverables via `manages` + `delivers` composition encoded in a `fun`. The KG returns **derived** facts **on demand** without duplicate storage.

**Guardrail mapping:** encode **closure** of permissions, **transitive** approvals, **implicit** prohibitions (via `not` + functions) as **reusable** checks MCP can call.

## RAG + agentic workflows

The chapter sketches customer-service and supply-chain flows: graph queries gather **multi-entity** context before LLM synthesis.

**RPA angle:** before clicking/UI automation, run **graph checks** (inventory, account state, open exceptions) then pass **compact** structured results to the model for **narration** or **branching**—not the other way around.

## Practical discipline

1. **Version** the shadow ontology with migrations (same as you would schema migrations).

2. **Monitor entropy**: orphan types, unused relations, ad hoc attributes—sign the ontology is losing **closure**.

3. **Test** critical `fun` paths like unit tests; empty vs. non-empty `match` is your **boolean** in CWA-style guards.
