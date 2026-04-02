# Hypergraphs, metagraphs, spacetime, memory, promises (book ch. 13–19)

Condensed **structural** insights for guard rails and RPA audit—not full tutorials.

## Hypergraphs (ch. 13 / “PERA as hyperedges”)

- **Hyperedge** = one relationship among **many** participants with **roles**.
- Property graphs: **reification** (fake intermediate nodes) → **proliferation**, **verbose** queries, weaker **joint** integrity.
- TypeDB **relation** = hyperedge with identity + attributes + type-checked role players.

**Guardrail use:** model each **automation context** (who, what, account, amount, channel, case id) as **one** relation so rules cannot “half apply” to fragments.

## Metagraphs (ch. 14–16)

**Metagraph** = relationships that connect **other** relationships (e.g. causality between events that are themselves relations). Property graphs need **bipartite E-node** workarounds; TypeDB lets **relations play roles** in higher relations natively.

**Guardrail use:**

- **Step A** `permitted_transition` **caused** **step B** `ui_action`.
- **Appeal** or **override** relations reference the **original** violation relation instance—clean **audit trail**.

## Semantic spacetime (ch. 18, Burgess / Promise theory framing)

Two axes: **semantic space** (similarity, containment, properties) and **time** (validity, causality, sequence). Four primitive **edge families**: **NEAR**, **CONTAINS**, **EXPRESSES** (property at time), **LEADS_TO**.

**Guardrail use:**

- **Effective dating** for policies (`valid-from` / `valid-to` on rule application or relation).
- **Causal** explanations for denials (“rule R1 fired **because** event E1 **LEADS_TO** state S”).

## AI agent memory (ch. 17)

Critique of **pure RAG**: similarity ≠ memory; opposite sentiments can be **too close** in embedding space; human-like memory blends **episodic** (dated events) and **semantic** (stable facts) and **meta-memory** (why we believe X).

**Guardrail use:** do **not** rely on embeddings for **hard** allow/deny. Optionally use episodic logging in TypeDB for **“similar past failures”** explanations **after** structural checks pass/fail.

**Five-layer reference architecture** (storage, search, extraction, chunking, schema discovery): for guard rails, **storage + schema** are essential; **vector search** and **schema discovery** are optional maturity stages.

## Promise graphs (ch. 19)

**Promise theory**: autonomy, voluntary commitments, bilateral coordination, **assessment** over central enforcement, local knowledge. TypeDB schemas for **promise**, **assessment**, **action**, **decision**, **attestation**, **reputation**.

**Guardrail use:** when **multiple services or vendors** contribute to one RPA flow, represent **commitments** (“provider promises response within T”) and **assessments** (“kept/broken”) as typed data—useful for **governance**, SLAs, and **tiered** trust, not only boolean rules.

## Open / closed world (cross-link ch. 11)

Metagraph and spacetime models assume you **know** what you stored; **planning** and **negation-as-failure** align with **CWA** in the **operational** slice. Combine with explicit **unknown** states in MCP when **extract** did not load a slice yet.

## Summary table

| Mechanism | Guardrail role |
|-----------|------------------|
| Hypergraph relations | One typed “fact” for multi-party checks |
| Metagraph | Audit: rules about rules; overrides; causality |
| Semantic spacetime | Time-bounded policy; causal traces |
| Structured memory | Optional explanations; avoid vector-only safety |
| Promise graphs | Multi-party SLA/trust alongside boolean logic |
