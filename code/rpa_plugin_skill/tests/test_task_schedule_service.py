from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.task_schedule_service import (
    list_task_schedules,
    upsert_task_schedule,
)


class TaskScheduleServiceTests(unittest.TestCase):
    @patch("rpa_plugin_skill.core.task_schedule_service.LayerCStore")
    def test_upsert_task_schedule_preview(self, store_cls: Mock) -> None:
        cfg = AppConfig.from_env()
        preview = upsert_task_schedule(
            config=cfg,
            registration_id="sql-medical-alpha",
            task_id="task-001",
            schedule_id="sched-001",
            mode="cron",
            cron_expression="*/15 * * * *",
            openclaw_job_ref="openclaw-job-001",
            enabled=True,
        )
        self.assertEqual(preview.schedule_id, "sched-001")
        self.assertEqual(preview.schedule_mode, "cron")
        self.assertTrue(preview.schedule_enabled)
        store_cls.return_value.upsert_task_schedule.assert_called_once()

    @patch("rpa_plugin_skill.core.task_schedule_service.LayerCStore")
    def test_list_task_schedules_passthrough(self, store_cls: Mock) -> None:
        cfg = AppConfig.from_env()
        store_cls.return_value.fetch_task_schedules_for_source.return_value = [
            {"schedule_id": "sched-001"}
        ]
        docs = list_task_schedules(cfg, "sql-medical-alpha")
        self.assertEqual(len(docs), 1)
        self.assertEqual(str(docs[0].get("schedule_id")), "sched-001")


if __name__ == "__main__":
    unittest.main()
