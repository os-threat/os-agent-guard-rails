from __future__ import annotations

import unittest
from dataclasses import replace

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.database_lifecycle import layer_a_db_name
from rpa_plugin_skill.core.rule_service import (
    archive_rule_for_source,
    delete_rule_for_source,
    list_rules_for_source,
    upsert_rule_for_source,
)
from rpa_plugin_skill.core.sql_registration_service import register_sql_source
from rpa_plugin_skill.core.typedb_bootstrap import connect_with_retry

SAMPLE_DDL = """
CREATE TABLE clients (
  id INT PRIMARY KEY,
  name VARCHAR(100)
);
"""

RULE_TYPEQL = """
define
  attribute gr_flag_high_risk, value boolean;
"""


class RuleServiceIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        base = AppConfig.from_env()
        self.cfg = replace(base, typedb_connect_retries=1, typedb_connect_retry_delay_sec=0.1)
        self.registration_id = "sql-rules-alpha"
        try:
            driver = connect_with_retry(self.cfg)
            driver.close()
        except Exception:
            self.skipTest("TypeDB not available for rule CRUD integration test")

        register_sql_source(
            config=self.cfg,
            source_name="Rules Alpha",
            ddl_source=SAMPLE_DDL,
            source_url="postgres://rules-alpha",
            registration_id=self.registration_id,
        )

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

    def test_rule_upsert_archive_and_delete(self) -> None:
        upsert_rule_for_source(
            config=self.cfg,
            registration_id=self.registration_id,
            rule_id="FP-R01",
            rule_name="Diversification threshold",
            nl_text="If risk tier is conservative, cap high-volatility allocations",
            horn_text="deny(X) :- conservative(X), high_volatility_allocation(X).",
            typeql_fun=RULE_TYPEQL,
            ast_ref="ast://fp-r01",
            status="active",
            apply_layer_a_logic=False,
        )

        listed = list_rules_for_source(self.cfg, self.registration_id)
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["rule_id"], "FP-R01")
        self.assertEqual(listed[0]["rule_status"], "active")

        archive_rule_for_source(self.cfg, self.registration_id, "FP-R01")
        listed_after_archive = list_rules_for_source(self.cfg, self.registration_id)
        self.assertEqual(listed_after_archive[0]["rule_status"], "archived")

        delete_rule_for_source(self.cfg, self.registration_id, "FP-R01")
        listed_after_delete = list_rules_for_source(self.cfg, self.registration_id)
        self.assertEqual(listed_after_delete, [])


if __name__ == "__main__":
    unittest.main()
