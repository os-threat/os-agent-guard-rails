from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig
from .layer_c_store import LayerCStore


@dataclass(frozen=True)
class TaskPreview:
    registration_id: str
    task_id: str
    task_name: str
    task_status: str
    extract_plan_ref: str


def upsert_task_for_source(
    config: AppConfig,
    registration_id: str,
    task_id: str,
    task_name: str,
    task_description: str,
    extract_plan_ref: str,
    status: str = "draft",
) -> TaskPreview:
    store = LayerCStore(config, ensure_schema=True)
    store.upsert_task(
        registration_id=registration_id,
        task_id=task_id,
        task_name=task_name,
        task_description=task_description,
        extract_plan_ref=extract_plan_ref,
        status=status,
    )
    return TaskPreview(
        registration_id=registration_id,
        task_id=task_id,
        task_name=task_name,
        task_status=status,
        extract_plan_ref=extract_plan_ref,
    )


def list_tasks_for_source(config: AppConfig, registration_id: str) -> list[dict]:
    store = LayerCStore(config, ensure_schema=True)
    return store.fetch_tasks_for_source(registration_id)


def set_task_status_for_source(config: AppConfig, task_id: str, status: str) -> None:
    store = LayerCStore(config, ensure_schema=True)
    store.set_task_status(task_id=task_id, status=status)


def delete_task_for_source(config: AppConfig, registration_id: str, task_id: str) -> None:
    store = LayerCStore(config, ensure_schema=True)
    store.delete_task(registration_id=registration_id, task_id=task_id)
