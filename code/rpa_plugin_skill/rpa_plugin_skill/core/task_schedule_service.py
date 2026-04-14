from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig
from .layer_c_store import LayerCStore


@dataclass(frozen=True)
class TaskSchedulePreview:
    registration_id: str
    task_id: str
    schedule_id: str
    schedule_mode: str
    cron_expression: str
    openclaw_job_ref: str
    schedule_enabled: bool


def upsert_task_schedule(
    config: AppConfig,
    registration_id: str,
    task_id: str,
    schedule_id: str,
    mode: str,
    cron_expression: str,
    openclaw_job_ref: str,
    enabled: bool,
    schedule_at_iso: str | None = None,
) -> TaskSchedulePreview:
    store = LayerCStore(config, ensure_schema=True)
    store.upsert_task_schedule(
        task_id=task_id,
        schedule_id=schedule_id,
        mode=mode,
        cron_expression=cron_expression,
        openclaw_job_ref=openclaw_job_ref,
        enabled=enabled,
        schedule_at_iso=schedule_at_iso,
    )
    return TaskSchedulePreview(
        registration_id=registration_id,
        task_id=task_id,
        schedule_id=schedule_id,
        schedule_mode=mode,
        cron_expression=cron_expression,
        openclaw_job_ref=openclaw_job_ref,
        schedule_enabled=enabled,
    )


def list_task_schedules(config: AppConfig, registration_id: str) -> list[dict]:
    store = LayerCStore(config, ensure_schema=True)
    return store.fetch_task_schedules_for_source(registration_id)
