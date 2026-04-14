# Rules Composer UI contract (issue #55)

This module implements the Rule Composer flow from the overview Basic Flow:

- left pane: natural language rule text
- right pane tab 1: Logic viewer (`Horn IF/THEN/ELSE` + diagram)
- right pane tab 2: TypeQL viewer (generated `fun`, read-only or propose-diff mode)

## Basic flow alignment

1. User writes NL rule text.
2. Composer produces Horn-style IF/THEN/ELSE rendering for review.
3. Composer renders a logic diagram (Mermaid) for visual inspection.
4. Composer generates TypeQL `fun` query text in schema-transaction style.
5. User can store/activate using existing rule CRUD service.

## TypeQL tab style

Generated TypeQL uses `fun` style from `skills/typedb/SKILL.md`:

- function is inside a `redefine` block
- semicolon-terminated statements inside `match` and `return`
- boolean guard semantics via explicit `return true;` or `return false;`

Example shape:

```typeql
redefine
  fun gr_guard_fp_r01($subject_key: string) -> boolean:
    match
      $subject isa gra_client, has gra_client_id == $subject_key;
    return false;
```

## CLI preview

`python -m rpa_plugin_skill --rule-compose-preview --rule-id FP-R01 --rule-name "Diversification threshold" --rule-nl "If concentration is high then deny else allow"`

The command prints NL + logic tab + TypeQL tab payload that a UI can render directly.
