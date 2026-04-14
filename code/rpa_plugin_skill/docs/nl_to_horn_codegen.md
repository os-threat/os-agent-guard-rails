# NL -> Horn AST -> TypeQL codegen (issue #56)

This stage adds deterministic NL rule compilation before writing to TypeDB.

## Pipeline

1. Parse natural language into AST (`RuleAst`)
2. Generate Horn IF/THEN/ELSE clause from AST
3. Generate TypeQL `fun` fragment in `redefine` block
4. Validate fragments (including semicolon-terminated TypeQL statements)
5. Persist AST reference string in Layer C (`gr_rule_ast_ref`)
6. Apply generated `redefine` query in Layer A schema transaction

## Supported NL shape

`If <condition> then <allow|deny> [else <allow|deny>]`

Example:

- `If concentration is high then deny else allow`

## Validation and actionable errors

Compilation raises `RuleValidationError` with explicit guidance:

- empty rule text -> "Rule text is empty..."
- invalid structure -> "Rule must match 'If <condition> then <allow|deny> [else <allow|deny>]'."
- malformed TypeQL fragments -> semicolon/structure error including the exact offending line

## Fixtures and unit tests

AST fixtures:

- `tests/fixtures/rule_ast/valid_fp_r01.json`
- `tests/fixtures/rule_ast/invalid_missing_if_then.json`

Tests:

- `tests/test_nl_rule_codegen.py`

## CLI integration

Use codegen-backed upsert:

```bash
python -m rpa_plugin_skill --rule-upsert --rule-codegen-from-nl --rule-source sql-financial-main --rule-id FP-R01 --rule-name "Diversification threshold" --rule-nl "If concentration is high then deny else allow" --rule-status active
```

Invalid rules are blocked before schema commit with actionable errors.
