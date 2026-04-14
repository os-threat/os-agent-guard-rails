from __future__ import annotations

import json
from dataclasses import dataclass

from .config import AppConfig
from .layer_c_store import LayerCStore
from .openapi_to_typeql import ExtractBundle
from .rest_sync_worker import RestSyncPlan, sync_rest_bundle_to_layer_a
from .sql_sync_worker import SqlSyncPlan, sync_sql_rows_to_layer_a
from .task_composer import TaskComposerPreview, compose_task_preview


@dataclass(frozen=True)
class TaskLoadPreview:
    registration_id: str
    task_id: str
    task_status: str
    source_kind: str
    rows_loaded: int
    plan_summary: str
    extract_plan_ref: str


class TaskPlanError(ValueError):
    """Raised when task description cannot be planned against source metadata."""


def prepare_task_for_schedule(
    config: AppConfig,
    registration_id: str,
    task_id: str,
    task_name: str,
    task_description: str,
) -> TaskLoadPreview:
    store = LayerCStore(config, ensure_schema=True)
    source = store.fetch_registered_source(registration_id)
    if not source:
        raise TaskPlanError(f"Unknown registration_id: {registration_id}")

    source_kind = str(source.get("source_kind", "")).strip()
    source_url = str(source.get("source_url", "")).strip()
    if source_kind not in {"sql", "api"}:
        raise TaskPlanError(f"Unsupported source_kind for task planning: {source_kind}")
    if not source_url:
        raise TaskPlanError("Source URL is required for task planning")

    composer = compose_task_preview(
        config=config,
        registration_id=registration_id,
        description=task_description,
    )
    target = _infer_target(composer)

    if source_kind == "sql":
        sql_query = f"SELECT * FROM {target}"
        sql_plan = SqlSyncPlan(
            registration_id=registration_id,
            sql_dsn=source_url,
            sql_query=sql_query,
            source_table=target,
        )
        result = sync_sql_rows_to_layer_a(config, sql_plan)
        rows_loaded = result.rows_synced
        plan_payload = {
            "plan_kind": "sql",
            "source_table": target,
            "sql_query": sql_query,
            "rows_loaded": rows_loaded,
            "layer_a_db": result.layer_a_db,
        }
    else:
        entity = target if target.startswith("gra_") else f"gra_{target}"
        path = f"/{target.replace('_', '-')}"
        rest_plan = RestSyncPlan(
            registration_id=registration_id,
            base_url=source_url,
            bundle=ExtractBundle(
                operation_id=f"task-{task_id}",
                method="GET",
                path=path,
                source_pointer=path,
                response_jsonpath="$.data[*]",
                parameter_bindings={},
            ),
            target_entity=entity,
            response_records_key="data",
            max_pages=1,
        )
        result = sync_rest_bundle_to_layer_a(config, rest_plan)
        rows_loaded = result.rows_synced
        plan_payload = {
            "plan_kind": "api",
            "path": path,
            "method": "GET",
            "target_entity": entity,
            "rows_loaded": rows_loaded,
            "layer_a_db": result.layer_a_db,
        }

    extract_plan_ref = json.dumps(plan_payload, ensure_ascii=True, sort_keys=True)
    store.upsert_task(
        registration_id=registration_id,
        task_id=task_id,
        task_name=task_name,
        task_description=task_description,
        extract_plan_ref=extract_plan_ref,
        status="ready",
    )
    return TaskLoadPreview(
        registration_id=registration_id,
        task_id=task_id,
        task_status="ready",
        source_kind=source_kind,
        rows_loaded=rows_loaded,
        plan_summary=extract_plan_ref,
        extract_plan_ref=extract_plan_ref,
    )


def _infer_target(composer: TaskComposerPreview) -> str:
    if composer.highlighted_objects:
        candidate = composer.highlighted_objects[0].label
        if candidate.startswith("gra_"):
            return candidate.removeprefix("gra_")
        return candidate
    words = [w for w in composer.description.lower().split() if w.isalpha()]
    if words:
        return words[-1].rstrip("s")
    return "records"
