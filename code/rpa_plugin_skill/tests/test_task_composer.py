from __future__ import annotations

import unittest

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.task_composer import compose_task_preview


class TaskComposerTests(unittest.TestCase):
    def test_schema_aware_highlights_and_flow_preview(self) -> None:
        cfg = AppConfig.from_env()
        schema_text = """
define
  entity gra_client;
  entity gra_task;
  attribute gra_client_id, value string;
"""
        preview = compose_task_preview(
            config=cfg,
            registration_id="sql-medical-alpha",
            description="Extract client records, validate, then schedule review task",
            schema_text=schema_text,
        )

        labels = [item.label for item in preview.highlighted_objects]
        self.assertIn("gra_client", labels)
        self.assertIn("gra_task", labels)
        self.assertIn("extract", preview.highlighted_process_terms)
        self.assertIn("validate", preview.highlighted_process_terms)
        self.assertIn("schedule", preview.highlighted_process_terms)
        self.assertIn("Schema Objects", preview.diagram_mermaid)
        self.assertEqual(len(preview.flow_steps), 5)

    def test_preview_without_schema_match_uses_fallback(self) -> None:
        cfg = AppConfig.from_env()
        preview = compose_task_preview(
            config=cfg,
            registration_id="api-financial-main",
            description="Notify and review outbound communications",
            schema_text="define\n  entity gra_portfolio;",
        )
        self.assertEqual(preview.highlighted_objects, [])
        self.assertIn("notify", preview.highlighted_process_terms)
        self.assertIn("review", preview.highlighted_process_terms)
        self.assertIn("no-schema-match", preview.diagram_mermaid)


if __name__ == "__main__":
    unittest.main()
