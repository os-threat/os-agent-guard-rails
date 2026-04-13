from __future__ import annotations

import unittest
import uuid
from dataclasses import replace
from pathlib import Path

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.database_lifecycle import layer_a_db_name
from rpa_plugin_skill.core.sql_ddl_ingest import parse_postgres_ddl
from rpa_plugin_skill.core.sql_to_typeql import apply_layer_a_schema, generate_define_from_ddl
from rpa_plugin_skill.core.typedb_bootstrap import connect_with_retry

SAMPLE_DDL = """
CREATE TABLE patients (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE prescriptions (
    id INT PRIMARY KEY,
    patient_id INT REFERENCES patients(id)
);
"""


class SqlToTypeQLTests(unittest.TestCase):
    def test_generate_matches_golden_file(self) -> None:
        model = parse_postgres_ddl(SAMPLE_DDL)
        generated = generate_define_from_ddl(model, namespace="gra")

        golden_path = Path(__file__).parent / "golden" / "sql_to_typeql_sample.tql"
        expected = golden_path.read_text(encoding="utf-8")
        self.assertEqual(generated.strip(), expected.strip())

    def test_composite_primary_key_gets_synthetic_key(self) -> None:
        ddl = """
        CREATE TABLE bridge (
            left_id INT,
            right_id INT,
            PRIMARY KEY (left_id, right_id)
        );
        """
        model = parse_postgres_ddl(ddl)
        generated = generate_define_from_ddl(model, namespace="gra")
        self.assertIn("attribute gra_bridge_composite_key, value string;", generated)
        self.assertIn("owns gra_bridge_composite_key @key", generated)


class SqlToTypeQLIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        base = AppConfig.from_env()
        self.cfg = replace(
            base,
            typedb_connect_retries=1,
            typedb_connect_retry_delay_sec=0.1,
            layer_c_db=f"layer_c_sql2tql_{suffix}",
            layer_b_db=f"layer_b_sql2tql_{suffix}",
            layer_a_test_db=f"layer_a_sql2tql_{suffix}",
        )

        try:
            driver = connect_with_retry(self.cfg)
            driver.close()
        except Exception:
            self.skipTest("TypeDB not available for Layer A schema integration test")

    def tearDown(self) -> None:
        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            return
        try:
            db_name = layer_a_db_name(self.cfg, "sql2typeql-registration")
            if driver.databases.contains(db_name):
                driver.databases.get(db_name).delete()
        finally:
            driver.close()

    def test_apply_schema_targets_named_layer_a_db(self) -> None:
        model = parse_postgres_ddl("CREATE TABLE sample (id INT PRIMARY KEY, note TEXT);")
        query = generate_define_from_ddl(model, namespace="gra")
        result = apply_layer_a_schema(
            self.cfg,
            registration_id="sql2typeql-registration",
            define_query=query,
            redefine=False,
        )

        expected_db = layer_a_db_name(self.cfg, "sql2typeql-registration")
        self.assertEqual(result.layer_a_db, expected_db)

        driver = connect_with_retry(self.cfg)
        try:
            schema_text = driver.databases.get(expected_db).schema()
            self.assertIn("entity gra_sample", schema_text)
            self.assertIn("owns gra_sample_id @key", schema_text)
        finally:
            driver.close()


if __name__ == "__main__":
    unittest.main()
