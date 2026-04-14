from __future__ import annotations

import unittest

from rpa_plugin_skill.core.rule_composer import compose_rule_preview


class RuleComposerTests(unittest.TestCase):
    def test_preview_contains_nl_horn_and_typeql_fun_tabs(self) -> None:
        preview = compose_rule_preview(
            rule_id="FP-R01",
            rule_name="Diversification threshold",
            nl_text="If concentration is high then deny else allow",
        )

        self.assertEqual(preview.nl_text, "If concentration is high then deny else allow")
        self.assertIn("deny(gr_guard_fp_r01)", preview.logic_tab.horn_clause)
        self.assertIn("flowchart LR", preview.logic_tab.diagram_mermaid)
        self.assertIn("fun gr_guard_fp_r01", preview.typeql_tab.function_define_query)
        self.assertIn("return false;", preview.typeql_tab.function_define_query)
        self.assertTrue(preview.ast_ref.startswith("ast-json://"))

    def test_typeql_fun_style_is_redefine_plus_semicolon_terminated(self) -> None:
        preview = compose_rule_preview(
            rule_id="FP-R20",
            rule_name="Trace id required",
            nl_text="If trace id is missing then deny else allow",
            target_entity="gra_task",
            target_key_attribute="gra_task_id",
        )

        query = preview.typeql_tab.function_define_query
        self.assertTrue(query.startswith("redefine\n"))
        self.assertIn("fun gr_guard_fp_r20($subject_key: string) -> boolean:", query)
        self.assertIn("$subject isa gra_task, has gra_task_id == $subject_key;", query)
        self.assertTrue(query.strip().endswith("return false;"))


if __name__ == "__main__":
    unittest.main()
