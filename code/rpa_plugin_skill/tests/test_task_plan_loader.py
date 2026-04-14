from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.rest_sync_worker import RestSyncResult
from rpa_plugin_skill.core.sql_sync_worker import SqlSyncResult
from rpa_plugin_skill.core.task_composer import FlowStep, HighlightTerm, TaskComposerPreview
from rpa_plugin_skill.core.task_plan_loader import prepare_task_for_schedule


class TaskPlanLoaderTests(unittest.TestCase):
    @patch("rpa_plugin_skill.core.task_plan_loader.sync_sql_rows_to_layer_a")
    @patch("rpa_plugin_skill.core.task_plan_loader.compose_task_preview")
    @patch("rpa_plugin_skill.core.task_plan_loader.LayerCStore")
    def test_sql_task_prepare_sets_ready_and_returns_row_preview(
        self,
        store_cls: Mock,
        compose_preview: Mock,
        sync_sql: Mock,
    ) -> None:
        cfg = AppConfig.from_env()
        store = store_cls.return_value
        store.fetch_registered_source.return_value = {
            "registration_id": "sql-medical-alpha",
            "source_kind": "sql",
            "source_url": "postgresql://demo/demo",
            "source_is_active": True,
        }
        compose_preview.return_value = TaskComposerPreview(
            registration_id="sql-medical-alpha",
            description="Extract clients and review",
            layer_a_db="layer_a_demo",
            highlighted_objects=[HighlightTerm(label="clients", kind="entity")],
            highlighted_process_terms=["extract", "review"],
            flow_steps=[FlowStep("extract", "Extract", "Extract rows")],
            diagram_mermaid="flowchart LR",
        )
        sync_sql.return_value = SqlSyncResult(
            registration_id="sql-medical-alpha",
            layer_a_db="layer_a_demo",
            rows_synced=12,
            watermark_max=None,
        )

        preview = prepare_task_for_schedule(
            config=cfg,
            registration_id="sql-medical-alpha",
            task_id="task-001",
            task_name="Load clients",
            task_description="Extract clients and review",
        )

        self.assertEqual(preview.task_status, "ready")
        self.assertEqual(preview.rows_loaded, 12)
        store.upsert_task.assert_called_once()
        args = store.upsert_task.call_args.kwargs
        self.assertEqual(args["status"], "ready")
        self.assertIn("sql", args["extract_plan_ref"])

    @patch("rpa_plugin_skill.core.task_plan_loader.sync_rest_bundle_to_layer_a")
    @patch("rpa_plugin_skill.core.task_plan_loader.compose_task_preview")
    @patch("rpa_plugin_skill.core.task_plan_loader.LayerCStore")
    def test_api_task_prepare_sets_ready_and_returns_row_preview(
        self,
        store_cls: Mock,
        compose_preview: Mock,
        sync_rest: Mock,
    ) -> None:
        cfg = AppConfig.from_env()
        store = store_cls.return_value
        store.fetch_registered_source.return_value = {
            "registration_id": "api-financial-main",
            "source_kind": "api",
            "source_url": "http://localhost:4010/v1",
            "source_is_active": True,
        }
        compose_preview.return_value = TaskComposerPreview(
            registration_id="api-financial-main",
            description="Extract households and approve recommendations",
            layer_a_db="layer_a_demo",
            highlighted_objects=[HighlightTerm(label="gra_household", kind="entity")],
            highlighted_process_terms=["extract", "approve"],
            flow_steps=[FlowStep("extract", "Extract", "Extract rows")],
            diagram_mermaid="flowchart LR",
        )
        sync_rest.return_value = RestSyncResult(
            registration_id="api-financial-main",
            layer_a_db="layer_a_demo",
            pages_fetched=1,
            rows_synced=8,
        )

        preview = prepare_task_for_schedule(
            config=cfg,
            registration_id="api-financial-main",
            task_id="task-101",
            task_name="Load households",
            task_description="Extract households and approve recommendations",
        )

        self.assertEqual(preview.task_status, "ready")
        self.assertEqual(preview.rows_loaded, 8)
        store.upsert_task.assert_called_once()
        args = store.upsert_task.call_args.kwargs
        self.assertEqual(args["status"], "ready")
        self.assertIn("\"plan_kind\": \"api\"", args["extract_plan_ref"])


if __name__ == "__main__":
    unittest.main()
