from __future__ import annotations

import os
import unittest
import uuid

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.layer_b_migrations import (
    apply_layer_b_migrations,
    schema_contains_marker,
)
from rpa_plugin_skill.core.typedb_bootstrap import connect_with_retry


class LayerBMigrationTests(unittest.TestCase):
    def test_marker_detection(self) -> None:
        schema = "define\n  entity grb_agent;"
        self.assertTrue(schema_contains_marker(schema, "grb_agent"))
        self.assertFalse(schema_contains_marker(schema, "grb_promise"))


class LayerBMigrationIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        self.cfg = AppConfig(
            typedb_address=os.environ.get("TYPEDB_ADDRESS", "127.0.0.1:1729"),
            typedb_user=os.environ.get("TYPEDB_USER", "admin"),
            typedb_password=os.environ.get("TYPEDB_PASSWORD", "password"),
            typedb_tls_enabled=False,
            typedb_connect_retries=1,
            typedb_connect_retry_delay_sec=0.1,
            layer_c_db=f"layer_c_bmig_{suffix}",
            layer_b_db=f"layer_b_mig_{suffix}",
            layer_a_test_db=f"layer_a_bmig_{suffix}",
            layer_a_prefix="guardrails_layer_a_",
            max_database_name_length=64,
        )

        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            self.skipTest("TypeDB not available for Layer B integration test")

        driver.databases.create(self.cfg.layer_c_db)
        driver.databases.create(self.cfg.layer_b_db)
        driver.close()

    def tearDown(self) -> None:
        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            return

        for db_name in (self.cfg.layer_c_db, self.cfg.layer_b_db):
            if driver.databases.contains(db_name):
                driver.databases.get(db_name).delete()
        driver.close()

    def test_apply_layer_b_schema(self) -> None:
        applied = apply_layer_b_migrations(self.cfg)
        self.assertTrue(applied)

        driver = connect_with_retry(self.cfg)
        try:
            schema_text = driver.databases.get(self.cfg.layer_b_db).schema()
            self.assertIn("grb_agent", schema_text)
            self.assertIn("grb_action_data_trace_binding", schema_text)
        finally:
            driver.close()


if __name__ == "__main__":
    unittest.main()
