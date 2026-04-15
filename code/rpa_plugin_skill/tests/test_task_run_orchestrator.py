from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.mcp_server import GuardInvocationResult
from rpa_plugin_skill.core.sql_sync_worker import SqlSyncResult
from rpa_plugin_skill.core.task_run_orchestrator import (
    TaskRunError,
    resync_task_layer_a_from_plan,
    run_task_orchestration,
)


class ResyncTaskLayerATests(unittest.TestCase):
    def test_empty_plan_raises(self) -> None:
        cfg = AppConfig.from_env()
        with self.assertRaises(TaskRunError):
            resync_task_layer_a_from_plan(cfg, "reg-x", "")

    @patch("rpa_plugin_skill.core.task_run_orchestrator.sync_sql_rows_to_layer_a")
    @patch("rpa_plugin_skill.core.task_run_orchestrator.LayerCStore")
    def test_sql_plan_uses_source_url(
        self,
        store_cls: MagicMock,
        sync_sql: MagicMock,
    ) -> None:
        cfg = AppConfig.from_env()
        store_cls.return_value.fetch_registered_source.return_value = {
            "source_url": "postgresql://example/db",
        }
        sync_sql.return_value = SqlSyncResult(
            registration_id="reg-x",
            layer_a_db="layer_a",
            rows_synced=4,
            watermark_max=None,
        )
        plan = {
            "plan_kind": "sql",
            "sql_query": "SELECT * FROM clients",
            "source_table": "clients",
        }
        n = resync_task_layer_a_from_plan(cfg, "reg-x", json.dumps(plan))
        self.assertEqual(n, 4)
        sync_sql.assert_called_once()


class TaskRunOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = AppConfig.from_env()
        self.task_row = {
            "task_id": "task-001",
            "task_name": "Demo task",
            "extract_plan_ref": json.dumps(
                {"plan_kind": "sql", "sql_query": "SELECT 1", "source_table": "t"}
            ),
            "task_status": "ready",
        }

    @patch("rpa_plugin_skill.core.task_run_orchestrator.resync_task_layer_a_from_plan")
    @patch("rpa_plugin_skill.core.task_run_orchestrator.LayerCStore")
    def test_deny_path_logs_assessment(
        self,
        store_cls: MagicMock,
        resync: MagicMock,
    ) -> None:
        store_cls.return_value.fetch_task_for_source.return_value = self.task_row
        resync.return_value = 1
        mcp = MagicMock()
        mcp.invoke_guard_tool.return_value = GuardInvocationResult(
            tool_name="guard.gr_test",
            registration_id="reg-a",
            subject_key="DENY",
            decision=False,
            data_trace={
                "rule_id": "R1",
                "schema_hash": "abc",
                "sync_watermark": "wm1",
            },
        )
        result = run_task_orchestration(
            self.cfg,
            "reg-a",
            "task-001",
            "guard.gr_test",
            "DENY",
            mcp_server=mcp,
        )
        self.assertEqual(result.path, "deny")
        self.assertFalse(result.precheck_passed)
        self.assertEqual(result.sync_rows_loaded, 1)
        self.assertIn("deny", result.phases_completed)
        calls = [c[0][0] for c in mcp.invoke_promise_tool.call_args_list]
        self.assertEqual(calls, ["promise.declare", "promise.assess"])
        assess_payload = mcp.invoke_promise_tool.call_args_list[1][0][1]
        self.assertEqual(assess_payload["outcome"], "deny")

    @patch("rpa_plugin_skill.core.task_run_orchestrator.resync_task_layer_a_from_plan")
    @patch("rpa_plugin_skill.core.task_run_orchestrator.LayerCStore")
    def test_act_path_chains_and_allows(
        self,
        store_cls: MagicMock,
        resync: MagicMock,
    ) -> None:
        store_cls.return_value.fetch_task_for_source.return_value = self.task_row
        resync.return_value = 2
        mcp = MagicMock()
        mcp.invoke_guard_tool.return_value = GuardInvocationResult(
            tool_name="guard.gr_test",
            registration_id="reg-a",
            subject_key="ALLOW",
            decision=True,
            data_trace={
                "rule_id": "R1",
                "schema_hash": "abc",
                "sync_watermark": "wm1",
            },
        )
        result = run_task_orchestration(
            self.cfg,
            "reg-a",
            "task-001",
            "guard.gr_test",
            "ALLOW",
            mcp_server=mcp,
        )
        self.assertEqual(result.path, "act")
        self.assertTrue(result.precheck_passed)
        self.assertEqual(result.rpa_steps[1], "guard_precheck_passed")
        calls = [c[0][0] for c in mcp.invoke_promise_tool.call_args_list]
        self.assertEqual(
            calls,
            ["promise.declare", "promise.chain", "promise.assess"],
        )
        chain_payload = mcp.invoke_promise_tool.call_args_list[1][0][1]
        self.assertEqual(chain_payload["task_id"], "task-001")
        allow_payload = mcp.invoke_promise_tool.call_args_list[2][0][1]
        self.assertEqual(allow_payload["outcome"], "allow")

    @patch("rpa_plugin_skill.core.task_run_orchestrator.LayerCStore")
    def test_missing_task_raises(self, store_cls: MagicMock) -> None:
        store_cls.return_value.fetch_task_for_source.return_value = None
        with self.assertRaises(TaskRunError):
            run_task_orchestration(
                self.cfg,
                "reg-a",
                "missing",
                "guard.x",
                "k",
                mcp_server=MagicMock(),
            )


if __name__ == "__main__":
    unittest.main()
