from __future__ import annotations

import unittest
import uuid
from dataclasses import replace

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.layer_b_migrations import apply_layer_b_migrations
from rpa_plugin_skill.core.mcp_server import PluginMcpServer
from rpa_plugin_skill.core.typedb_bootstrap import connect_with_retry


class PromiseMcpServiceIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        base = AppConfig.from_env()
        self.cfg = replace(
            base,
            typedb_connect_retries=1,
            typedb_connect_retry_delay_sec=0.1,
            layer_c_db=f"promise_mcp_c_{suffix}",
            layer_b_db=f"promise_mcp_b_{suffix}",
        )
        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            self.skipTest("TypeDB not available for Promise MCP integration test")

        driver.databases.create(self.cfg.layer_c_db)
        driver.databases.create(self.cfg.layer_b_db)
        driver.close()
        apply_layer_b_migrations(self.cfg)

    def tearDown(self) -> None:
        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            return
        try:
            for db_name in (self.cfg.layer_b_db, self.cfg.layer_c_db):
                if driver.databases.contains(db_name):
                    driver.databases.get(db_name).delete()
        finally:
            driver.close()

    def test_declare_chain_assess_query_contract(self) -> None:
        server = PluginMcpServer(self.cfg)
        declared = server.invoke_promise_tool(
            "promise.declare",
            {
                "creator_id": "agent-a",
                "creator_name": "Agent A",
                "target_id": "agent-b",
                "target_name": "Agent B",
                "promise_id": "promise-001",
                "promise_title": "Validate treatment reminders",
                "promise_state": "accepted",
            },
        )
        self.assertEqual(declared.payload["promise_state"], "accepted")

        chained = server.invoke_promise_tool(
            "promise.chain",
            {
                "task_id": "task-001",
                "task_name": "Reminder task",
                "promise_id": "promise-001",
            },
        )
        self.assertEqual(chained.payload["task_id"], "task-001")

        assessed = server.invoke_promise_tool(
            "promise.assess",
            {
                "assessor_id": "agent-a",
                "assessor_name": "Agent A",
                "assessment_id": "assessment-001",
                "outcome": "allow",
                "notes": "Passed all checks",
                "promise_id": "promise-001",
            },
        )
        self.assertEqual(assessed.payload["outcome"], "allow")

        queried = server.invoke_promise_tool(
            "promise.query",
            {"promise_id": "promise-001"},
        )
        self.assertEqual(queried.payload["promise_id"], "promise-001")
        self.assertEqual(queried.payload["promise_state"], "accepted")
        self.assertEqual(queried.payload["assessment_count"], 1)

