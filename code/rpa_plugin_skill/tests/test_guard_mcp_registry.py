from __future__ import annotations

import unittest
from dataclasses import replace

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.database_lifecycle import layer_a_db_name
from rpa_plugin_skill.core.guard_mcp_registry import (
    GuardMcpRegistry,
    extract_typeql_function_label,
)
from rpa_plugin_skill.core.nl_rule_codegen import compile_nl_rule
from rpa_plugin_skill.core.rule_service import upsert_rule_for_source
from rpa_plugin_skill.core.sql_registration_service import register_sql_source
from rpa_plugin_skill.core.typedb_bootstrap import connect_with_retry

SAMPLE_DDL = """
CREATE TABLE doctors (
  id INT PRIMARY KEY,
  name VARCHAR(100)
);
"""


class GuardMcpRegistryUnitTests(unittest.TestCase):
    def test_extracts_fun_label_from_define_and_redefine(self) -> None:
        sample_define = (
            "define\n"
            "  fun gr_guard_x($k: string) -> boolean:\n"
            "    match $a isa x;\n"
            "    return check;\n"
        )
        self.assertEqual(extract_typeql_function_label(sample_define), "gr_guard_x")
        self.assertEqual(
            extract_typeql_function_label(
                "redefine\n  fun gr_guard_y($k: string) -> boolean:\n    return true;\n"
            ),
            "gr_guard_y",
        )

    def test_missing_fun_returns_none(self) -> None:
        self.assertIsNone(extract_typeql_function_label("define entity person;"))


class GuardMcpRegistryIntegrationTests(unittest.TestCase):
    """Hot reload: same registry instance gains tools after new rules without new process."""

    def setUp(self) -> None:
        base = AppConfig.from_env()
        self.cfg = replace(base, typedb_connect_retries=1, typedb_connect_retry_delay_sec=0.1)
        self.registration_id = "sql-mcp-hot-reload"
        try:
            driver = connect_with_retry(self.cfg)
            driver.close()
        except Exception:
            self.skipTest("TypeDB not available for Guard MCP registry integration test")

        register_sql_source(
            config=self.cfg,
            source_name="MCP Hot Reload",
            ddl_source=SAMPLE_DDL,
            source_url="postgres://mcp-hot",
            registration_id=self.registration_id,
        )
        self.registry = GuardMcpRegistry(self.cfg)

    def tearDown(self) -> None:
        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            return
        try:
            db_name = layer_a_db_name(self.cfg, self.registration_id)
            if driver.databases.contains(db_name):
                driver.databases.get(db_name).delete()
        finally:
            driver.close()

    def test_add_rule_then_refresh_shows_new_tool_without_new_registry(self) -> None:
        gen1 = self.registry.refresh(self.registration_id)
        self.assertEqual(gen1, 1)
        self.assertEqual(self.registry.list_tool_names(), ())

        first = compile_nl_rule("HR-01", "If a then deny else allow")
        upsert_rule_for_source(
            config=self.cfg,
            registration_id=self.registration_id,
            rule_id="HR-01",
            rule_name="First",
            nl_text="If a then deny else allow",
            horn_text=first.horn_clause,
            typeql_fun=first.redefine_fun_query,
            ast_ref=first.ast_ref,
            status="active",
            apply_layer_a_logic=False,
        )

        gen2 = self.registry.refresh(self.registration_id)
        self.assertEqual(gen2, 2)
        self.assertIn("gr_guard_hr_01", self.registry.list_tool_names())

        second = compile_nl_rule("HR-02", "If b then allow else deny")
        upsert_rule_for_source(
            config=self.cfg,
            registration_id=self.registration_id,
            rule_id="HR-02",
            rule_name="Second",
            nl_text="If b then allow else deny",
            horn_text=second.horn_clause,
            typeql_fun=second.redefine_fun_query,
            ast_ref=second.ast_ref,
            status="active",
            apply_layer_a_logic=False,
        )

        gen3 = self.registry.refresh(self.registration_id)
        self.assertEqual(gen3, 3)
        names = self.registry.list_tool_names()
        self.assertEqual(len(names), 2)
        self.assertIn("gr_guard_hr_01", names)
        self.assertIn("gr_guard_hr_02", names)


if __name__ == "__main__":
    unittest.main()
