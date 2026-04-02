# Source and scope

These notes condense ideas from **TypeDB for Edge AI Agents** (manuscript in [Volland/typedb-for-edge-ai-agents](https://github.com/Volland/typedb-for-edge-ai-agents/tree/main/manuscript), Leanpub: [TypeDB for Edge AI Agents](https://leanpub.com/typedbforedgeaiagents)).

They are written for this repo’s goal: **OpenClaw guard rails** using a TypeDB shadow of operational data, business rules, TypeQL functions, and a dynamically generated MCP surface so agents can validate RPA steps before execution.

The book’s framing is *edge AI agents* and *semantic memory*; here we map the same mechanics to **constraint checking, introspection, and provable preconditions** for automation.

## Article index

| File | Focus |
|------|--------|
| [01-why-traditional-databases-fail-agent-trust.md](01-why-traditional-databases-fail-agent-trust.md) | Vectors, SQL, documents, property graphs, RDF/OWL openness vs. agent meta-queries and trust |
| [02-when-typedb-shadowing-is-a-superior-guardrail.md](02-when-typedb-shadowing-is-a-superior-guardrail.md) | When a typed shadow + minimal extract wins; CWA; limits |
| [03-insights-for-typedb-guardrail-systems.md](03-insights-for-typedb-guardrail-systems.md) | Cross-chapter insight checklist mapped to this repo’s pipeline |
| [04-pera-and-polymorphism-for-guardrails.md](04-pera-and-polymorphism-for-guardrails.md) | PERA model; three polymorphisms; SQL inheritance hacks vs. native `sub` |
| [05-typeql-programmability-and-mcp.md](05-typeql-programmability-and-mcp.md) | Define/match/insert; type variables; `fun`; negation; aggregates → MCP tools |
| [06-queries-as-types-and-explainability.md](06-queries-as-types-and-explainability.md) | “Queries as types”; resolver as type checker; composability; formal papers |
| [07-owl-shacl-dl-vs-unified-types.md](07-owl-shacl-dl-vs-unified-types.md) | OWL/TBox–ABox, OWA cost, SHACL split brain, DL ceilings, dependent types unifying ontology + validation |
| [08-knowledge-graphs-entropy-and-hybrid-ai.md](08-knowledge-graphs-entropy-and-hybrid-ai.md) | Ontology vs. “random garbage”; inference functions; KG vs. vectors; RAG patterns |
| [09-typedb-3-edge-and-operations.md](09-typedb-3-edge-and-operations.md) | Rust/GC/latency, gRPC, functions vs. rules, `@card`/`@values`/`@range`, MPL 2.0 |
| [10-structures-memory-time-coordination.md](10-structures-memory-time-coordination.md) | Hypergraphs, metagraphs, semantic spacetime, agent memory layers, promise graphs—guardrail angles |
