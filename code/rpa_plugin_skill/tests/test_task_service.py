from __future__ import annotations

import unittest
import uuid
from dataclasses import replace

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.layer_c_store import LayerCStore, RegisteredSourceInput
from rpa_plugin_skill.core.task_service import (
    delete_task_for_source,
    list_tasks_for_source,
    set_task_status_for_source,
    upsert_task_for_source,
)
from rpa_plugin_skill.core.typedb_bootstrap import connect_with_retry


class TaskServiceIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        base = AppConfig.from_env()
        self.cfg = replace(
            base,
            typedb_connect_retries=1,
            typedb_connect_retry_delay_sec=0.1,
            layer_c_db=f"task_service_c_{suffix}",
            layer_b_db=f"task_service_b_{suffix}",
        )
        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            self.skipTest("TypeDB not available for Task Service integration test")

        driver.databases.create(self.cfg.layer_c_db)
        driver.databases.create(self.cfg.layer_b_db)
        driver.close()

        store = LayerCStore(self.cfg, ensure_schema=True)
        store.upsert_registered_source(
            RegisteredSourceInput(
                registration_id="reg-task-svc",
                source_name="Task Service Source",
                source_kind="sql",
                source_url="postgres://task-svc",
                source_description="task source for service tests",
                source_is_active=True,
                credential_ref_id="cred-task-svc",
                secret_provider="vault",
                secret_ref="vault://prod/task/service-creds",
            )
        )

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

    def test_task_service_crud(self) -> None:
        preview = upsert_task_for_source(
            config=self.cfg,
            registration_id="reg-task-svc",
            task_id="task-svc-001",
            task_name="Build extract plan",
            task_description="Create extraction plan from task description",
            extract_plan_ref="plan://task/001",
            status="draft",
        )
        self.assertEqual(preview.task_status, "draft")

        set_task_status_for_source(
            config=self.cfg,
            task_id="task-svc-001",
            status="ready",
        )
        docs = list_tasks_for_source(self.cfg, "reg-task-svc")
        self.assertEqual(len(docs), 1)
        rendered = str(docs[0])
        self.assertIn("task-svc-001", rendered)
        self.assertIn("ready", rendered)

        delete_task_for_source(
            config=self.cfg,
            registration_id="reg-task-svc",
            task_id="task-svc-001",
        )
        self.assertEqual(list_tasks_for_source(self.cfg, "reg-task-svc"), [])


if __name__ == "__main__":
    unittest.main()
