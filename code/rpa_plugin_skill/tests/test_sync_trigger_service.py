from __future__ import annotations

import os
import unittest
import uuid
from dataclasses import replace

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.sql_sync_worker import SqlSyncPlan
from rpa_plugin_skill.core.sync_trigger_service import (
    get_sync_status,
    trigger_manual_sql_sync,
    trigger_post_registration_sync,
    trigger_post_task_finalize_sync,
)
from rpa_plugin_skill.core.typedb_bootstrap import connect_with_retry


class SyncTriggerServiceIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        base = AppConfig.from_env()
        self.cfg = replace(
            base,
            typedb_connect_retries=1,
            typedb_connect_retry_delay_sec=0.1,
            layer_c_db=f"sync_trigger_c_{suffix}",
            layer_b_db=f"sync_trigger_b_{suffix}",
        )
        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            self.skipTest("TypeDB not available for sync trigger integration test")

        driver.databases.create(self.cfg.layer_c_db)
        driver.databases.create(self.cfg.layer_b_db)
        driver.close()

    def tearDown(self) -> None:
        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            return
        try:
            for db_name in (self.cfg.layer_c_db, self.cfg.layer_b_db):
                if driver.databases.contains(db_name):
                    driver.databases.get(db_name).delete()
        finally:
            driver.close()

    def test_post_registration_and_task_finalize_update_status(self) -> None:
        status1 = trigger_post_registration_sync(
            self.cfg, registration_id="sql-medical-alpha", source_kind="sql"
        )
        self.assertEqual(status1.last_sync_trigger, "post_registration:sql")
        self.assertIsNotNone(status1.last_sync_time)

        status2 = trigger_post_task_finalize_sync(
            self.cfg,
            registration_id="sql-medical-alpha",
            task_id="task-001",
        )
        self.assertEqual(status2.last_sync_trigger, "post_task_finalize:task-001")
        self.assertIsNotNone(status2.last_sync_time)

    def test_manual_sync_error_is_visible(self) -> None:
        plan = SqlSyncPlan(
            registration_id="sql-medical-alpha",
            sql_dsn=os.environ.get("SQL_SYNC_TEST_DSN", "postgresql://bad"),
            sql_query="SELECT 1 AS id",
            source_table="doctors",
            key_column="id",
        )
        with self.assertRaises(Exception):
            trigger_manual_sql_sync(self.cfg, plan)

        status = get_sync_status(self.cfg, "sql-medical-alpha")
        self.assertEqual(status.last_sync_trigger, "manual_sql_refresh")
        self.assertIsNotNone(status.last_sync_time)
        self.assertIsNotNone(status.last_sync_error)
        self.assertNotEqual(status.last_sync_error, "")

