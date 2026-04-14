from __future__ import annotations

import os
import unittest
from dataclasses import replace

from typedb.driver import TransactionType

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.database_lifecycle import layer_a_db_name
from rpa_plugin_skill.core.sql_registration_service import register_sql_source
from rpa_plugin_skill.core.sql_sync_worker import SqlSyncPlan, sync_sql_rows_to_layer_a
from rpa_plugin_skill.core.typedb_bootstrap import connect_with_retry

SAMPLE_DDL = """
CREATE TABLE doctors (
  id INT PRIMARY KEY,
  name VARCHAR(100)
);
"""


class SqlSyncWorkerIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        base = AppConfig.from_env()
        self.cfg = replace(base, typedb_connect_retries=1, typedb_connect_retry_delay_sec=0.1)
        self.registration_id = "sql-sync-medical-alpha"
        self.sql_dsn = os.environ.get("SQL_SYNC_TEST_DSN")
        try:
            driver = connect_with_retry(self.cfg)
            driver.close()
        except Exception:
            self.skipTest("TypeDB not available for SQL sync integration test")

        try:
            if not self.sql_dsn:
                self.skipTest("SQL_SYNC_TEST_DSN not set for Postgres sync integration test")
            import psycopg  # noqa: F401
            with psycopg.connect(self.sql_dsn, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
        except Exception:
            self.skipTest("Postgres not available for SQL sync integration test")

        register_sql_source(
            config=self.cfg,
            source_name="SQL Sync Medical Alpha",
            ddl_source=SAMPLE_DDL,
            source_url="postgres://medical-sync",
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

    def test_sync_rows_into_named_layer_a_db_with_idempotent_put(self) -> None:
        plan = SqlSyncPlan(
            registration_id=self.registration_id,
            sql_dsn=self.sql_dsn,
            sql_query="SELECT 1001::int AS id, 'Sync Doctor'::text AS name",
            source_table="doctors",
            key_column="id",
        )
        first = sync_sql_rows_to_layer_a(self.cfg, plan)
        second = sync_sql_rows_to_layer_a(self.cfg, plan)

        self.assertEqual(first.layer_a_db, layer_a_db_name(self.cfg, self.registration_id))
        self.assertEqual(first.rows_synced, 1)
        self.assertEqual(second.rows_synced, 1)

        driver = connect_with_retry(self.cfg)
        try:
            with driver.transaction(first.layer_a_db, TransactionType.READ) as tx:
                answer = tx.query(
                    """match
  $d isa gra_doctors,
    has gra_doctors_id $id,
    has gra_doctors_name $name;
  $id == 1001;
fetch {
  "id": $id,
  "name": $name
};"""
                ).resolve()
                self.assertTrue(answer.is_concept_documents())
                docs = list(answer.as_concept_documents())
                self.assertEqual(len(docs), 1)
        finally:
            driver.close()
