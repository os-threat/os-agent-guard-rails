# TypeDB 3.0, edge, and operations (book ch. 4)

## Rust rewrite — why the book cares

- **No GC pauses** → more **predictable latency** for local/edge checks (relevant if guard DB runs **beside** the agent).
- **Memory safety** claims (fewer crash classes in the engine).
- **Roughly 3–5×** query speedup vs 2.x cited in book; **p99** stability under load highlighted over peak throughput alone.

## Stack notes relevant to integration

- **gRPC** driver protocol — efficient for **service** embedding (your MCP server calling TypeDB).
- **RocksDB** under the hood — embedded-friendly footprint; book mentions smaller RAM targets than older Java era.
- **Async** API / tokio — if guard checks run in **Rust** or async hosts, align client style.

## Rules → functions

TypeDB **3.0** replaces older **rule** syntax with **`fun`** (composable, parameterized). This matches the manuscript’s examples throughout and aligns with **generated MCP** (one tool per function or small façade).

## Schema-level value constraints (examples from book)

- `@card(1..1)` on ownership — mandatory / uniqueness style constraints on attributes.
- `@values("online", "offline", "degraded")` — enumerated state machines for **status** fields.
- `@range(-50..150)` on numeric attributes — **bounds** enforced in DB.

**Guardrail use:** push **enum** and **range** policies into schema when they are **stable**; keeps checks **fast** and **consistent** across all tools without re-prompting the LLM.

## Licensing (MPL 2.0)

Community edition under **MPL 2.0**: commercial use allowed; modifications **to TypeDB itself** distributed to others need sharing—typical deployments **use** unmodified binaries + proprietary agent/MCP code remain fine (not legal advice—verify with your counsel for redistribution scenarios).

## Open source ecosystem

Book points to GitHub for **core + tools**; for this repo, pinning **versions** and automating **schema apply** in CI keeps generated MCP and TypeQL **reproducible**.

## Limitations acknowledged elsewhere

Native **ANN** / vector similarity inside TypeDB is **aspirational** in the “what comes next” chapter—plan **external** vector stores if you need first-class similarity **today**.

## Ops takeaway for guard rails

Treat TypeDB as a **local policy engine**: fast **enough** for per-step RPA validation, **schema-first** for enums/cardinality/ranges, **functions** as the **stable** API surface behind MCP.
