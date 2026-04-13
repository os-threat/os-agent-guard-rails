from __future__ import annotations

import unittest
from dataclasses import replace

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.database_lifecycle import layer_a_db_name
from rpa_plugin_skill.core.sql_registration_service import (
    expected_layer_a_db_for_registration,
    register_sql_source,
)
from rpa_plugin_skill.core.typedb_bootstrap import connect_with_retry

SAMPLE_DDL = """
CREATE TABLE doctors (
  id INT PRIMARY KEY,
  name VARCHAR(100)
);
"""


class SqlRegistrationServiceUnitTests(unittest.TestCase):
    def test_expected_layer_a_db_matches_lifecycle_mapping(self) -> None:
        cfg = AppConfig.from_env()
        reg_id = "sql-medical-main"
        self.assertEqual(
            expected_layer_a_db_for_registration(cfg, reg_id),
            layer_a_db_name(cfg, reg_id),
        )


class SqlRegistrationServiceIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        base = AppConfig.from_env()
        self.cfg = replace(base, typedb_connect_retries=1, typedb_connect_retry_delay_sec=0.1)
        try:
            driver = connect_with_retry(self.cfg)
            driver.close()
        except Exception:
            self.skipTest("TypeDB not available for SQL registration integration test")

    def tearDown(self) -> None:
        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            return
        try:
            for reg_id in ("sql-medical-alpha", "sql-medical-beta"):
                db_name = layer_a_db_name(self.cfg, reg_id)
                if driver.databases.contains(db_name):
                    driver.databases.get(db_name).delete()
        finally:
            driver.close()

    def test_multiple_sql_registrations_map_to_distinct_layer_a_dbs(self) -> None:
        first = register_sql_source(
            config=self.cfg,
            source_name="Medical Alpha",
            ddl_source=SAMPLE_DDL,
            source_url="postgres://alpha",
            registration_id="sql-medical-alpha",
        )
        second = register_sql_source(
            config=self.cfg,
            source_name="Medical Beta",
            ddl_source=SAMPLE_DDL,
            source_url="postgres://beta",
            registration_id="sql-medical-beta",
        )

        self.assertNotEqual(first.layer_a_db, second.layer_a_db)
        self.assertIn("doctors", first.tables)


if __name__ == "__main__":
    unittest.main()
