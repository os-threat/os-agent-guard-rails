from __future__ import annotations

import unittest
import uuid
from dataclasses import replace

from typedb.driver import TransactionType

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.database_lifecycle import layer_a_db_name
from rpa_plugin_skill.core.layer_c_store import LayerCStore, RegisteredSourceInput
from rpa_plugin_skill.core.mcp_server import PluginMcpServer
from rpa_plugin_skill.core.typedb_bootstrap import connect_with_retry


class GuardMcpInvokeIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        base = AppConfig.from_env()
        self.cfg = replace(
            base,
            typedb_connect_retries=1,
            typedb_connect_retry_delay_sec=0.1,
            layer_c_db=f"guard_mcp_c_{suffix}",
            layer_b_db=f"guard_mcp_b_{suffix}",
        )
        self.registration_id = "sql-guard-mcp-alpha"
        self.layer_a_db = layer_a_db_name(self.cfg, self.registration_id)
        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            self.skipTest("TypeDB not available for guard MCP invocation test")

        driver.databases.create(self.cfg.layer_c_db)
        driver.databases.create(self.cfg.layer_b_db)
        if not driver.databases.contains(self.layer_a_db):
            driver.databases.create(self.layer_a_db)
        with driver.transaction(self.layer_a_db, TransactionType.SCHEMA) as tx:
            tx.query(
                """define
  fun gr_guard_fp_r99($subject_key: string) -> boolean:
    match
      $label == $subject_key;
      $label == "ALLOW";
    return check;"""
            ).resolve()
            tx.commit()
        driver.close()

        store = LayerCStore(self.cfg, ensure_schema=True)
        store.upsert_registered_source(
            RegisteredSourceInput(
                registration_id=self.registration_id,
                source_name="Guard Source",
                source_kind="sql",
                source_url="postgres://x",
                source_description="test source",
                source_is_active=True,
                credential_ref_id=f"cred-{suffix}",
                secret_provider="env",
                secret_ref="env://DUMMY_DSN",
            )
        )
        store.upsert_rule(
            registration_id=self.registration_id,
            rule_id="FP-R99",
            rule_name="Allow Label Check",
            nl_text="If subject key equals ALLOW then allow else deny",
            horn_text="allow(gr_guard_fp_r99) :- subject(ALLOW).",
            typeql_fun=(
                "define\n"
                "  fun gr_guard_fp_r99($subject_key: string) -> boolean:\n"
                "    match\n"
                "      $label == $subject_key;\n"
                "      $label == \"ALLOW\";\n"
                "    return check;\n"
            ),
            ast_ref="ast-json://{}",
            status="active",
        )
        store.upsert_setting(
            f"sync:{self.registration_id}:last_sync_time",
            "2026-04-14T12:00:00Z",
        )

    def tearDown(self) -> None:
        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            return
        try:
            for db_name in (self.cfg.layer_c_db, self.cfg.layer_b_db, self.layer_a_db):
                if driver.databases.contains(db_name):
                    driver.databases.get(db_name).delete()
        finally:
            driver.close()

    def test_invoke_guard_tool_returns_decision_and_data_trace(self) -> None:
        server = PluginMcpServer(self.cfg)
        server.set_guard_source(self.registration_id)
        result = server.invoke_guard_tool("guard.gr_guard_fp_r99", "ALLOW")
        self.assertTrue(result.decision)
        self.assertEqual(result.data_trace["rule_id"], "FP-R99")
        self.assertEqual(
            result.data_trace["sync_watermark"],
            "2026-04-14T12:00:00Z",
        )
        self.assertIsNotNone(result.data_trace["schema_hash"])

