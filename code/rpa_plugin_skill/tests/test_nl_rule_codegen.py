from __future__ import annotations

import json
import unittest
from pathlib import Path

from rpa_plugin_skill.core.nl_rule_codegen import (
    RuleValidationError,
    compile_nl_rule,
)


class NLRuleCodegenFixtureTests(unittest.TestCase):
    def test_valid_fixture_compiles_to_ast_horn_and_redefine_fun(self) -> None:
        fixture = _read_fixture("valid_fp_r01.json")
        artifacts = compile_nl_rule("FP-R01", fixture["nl_text"])

        expected = fixture["expected"]
        self.assertEqual(artifacts.ast.condition_text, expected["condition_text"])
        self.assertEqual(artifacts.ast.then_action, expected["then_action"])
        self.assertEqual(artifacts.ast.else_action, expected["else_action"])
        self.assertEqual(artifacts.function_label, expected["function_label"])

        self.assertIn("deny(gr_guard_fp_r01)", artifacts.horn_clause)
        self.assertTrue(artifacts.redefine_fun_query.startswith("redefine\n"))
        self.assertIn(
            "fun gr_guard_fp_r01($subject_key: string) -> boolean:",
            artifacts.redefine_fun_query,
        )
        self.assertIn("return false;", artifacts.redefine_fun_query)

    def test_invalid_fixture_returns_actionable_error(self) -> None:
        fixture = _read_fixture("invalid_missing_if_then.json")
        with self.assertRaises(RuleValidationError) as ctx:
            compile_nl_rule("FP-R02", fixture["nl_text"])

        self.assertIn(fixture["expected_error_contains"], str(ctx.exception))


class NLRuleCodegenValidationTests(unittest.TestCase):
    def test_empty_rule_error_is_actionable(self) -> None:
        with self.assertRaises(RuleValidationError) as ctx:
            compile_nl_rule("FP-R03", "")
        self.assertIn("Rule text is empty", str(ctx.exception))


def _read_fixture(name: str) -> dict:
    path = Path(__file__).parent / "fixtures" / "rule_ast" / name
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
