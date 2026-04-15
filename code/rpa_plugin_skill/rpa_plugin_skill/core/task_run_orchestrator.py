"""PLAN §5.6 run state machine: Sync → Precheck (Guard) → Act or Deny → Review."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any

from .config import AppConfig
from .layer_c_store import LayerCStore
from .mcp_server import GuardToolInvocationError, PluginMcpServer
from .openapi_to_typeql import ExtractBundle
from .rest_sync_worker import RestSyncPlan, sync_rest_bundle_to_layer_a
from .sql_sync_worker import SqlSyncPlan, sync_sql_rows_to_layer_a


class TaskRunError(ValueError):
    """Raised when a task run cannot proceed (missing task, plan, or guard error)."""


@dataclass(frozen=True)
class TaskRunResult:
    """OpenClaw-friendly summary of one orchestrated task run."""

    registration_id: str
    task_id: str
    path: str  # "act" | "deny" | "error"
    phases_completed: tuple[str, ...]
    sync_rows_loaded: int
    guard_tool: str
    subject_key: str
    guard_decision: bool | None
    precheck_passed: bool
    promise_id: str | None
    assessment_id: str | None
    correlation_id: str | None
    rpa_steps: tuple[str, ...] = ()
    review: dict[str, Any] = field(default_factory=dict)


def resync_task_layer_a_from_plan(
    config: AppConfig,
    registration_id: str,
    extract_plan_ref: str,
) -> int:
    """Re-execute stored extract plan (SQL or REST) into Layer A."""
    text = extract_plan_ref.strip()
    if not text:
        raise TaskRunError(
            "Task extract_plan_ref is empty; run prepare_task_for_schedule first."
        )
    try:
        plan = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TaskRunError(f"Invalid extract_plan_ref JSON: {exc}") from exc

    store = LayerCStore(config, ensure_schema=True)
    source = store.fetch_registered_source(registration_id)
    if not source:
        raise TaskRunError(f"Unknown registration_id: {registration_id}")
    base_url = str(source.get("source_url", "") or "").strip()
    if not base_url:
        raise TaskRunError("Registered source has no source_url for resync")

    kind = plan.get("plan_kind")
    if kind == "sql":
        sql_query = str(plan.get("sql_query", "") or "").strip()
        source_table = str(plan.get("source_table", "") or "").strip()
        if not sql_query or not source_table:
            raise TaskRunError("SQL plan missing sql_query or source_table")
        sync_plan = SqlSyncPlan(
            registration_id=registration_id,
            sql_dsn=base_url,
            sql_query=sql_query,
            source_table=source_table,
        )
        result = sync_sql_rows_to_layer_a(config, sync_plan)
        return result.rows_synced

    if kind == "api":
        path = str(plan.get("path", "") or "").strip()
        target_entity = str(plan.get("target_entity", "") or "").strip()
        method = str(plan.get("method", "GET") or "GET").strip()
        if not path or not target_entity:
            raise TaskRunError("API plan missing path or target_entity")
        op_id = str(plan.get("operation_id", "task-resync"))
        bundle = ExtractBundle(
            operation_id=op_id,
            method=method,
            path=path,
            source_pointer=path,
            response_jsonpath="$.data[*]",
            parameter_bindings={},
        )
        rest_plan = RestSyncPlan(
            registration_id=registration_id,
            base_url=base_url.rstrip("/"),
            bundle=bundle,
            target_entity=target_entity,
            response_records_key="data",
            max_pages=1,
        )
        result = sync_rest_bundle_to_layer_a(config, rest_plan)
        return result.rows_synced

    raise TaskRunError(f"Unknown or missing plan_kind in extract plan: {kind!r}")


def run_task_orchestration(
    config: AppConfig,
    registration_id: str,
    task_id: str,
    guard_tool: str,
    subject_key: str,
    *,
    agent_id: str = "openclaw-runner",
    agent_name: str = "OpenClaw Runner",
    mcp_server: PluginMcpServer | None = None,
) -> TaskRunResult:
    """Sync, guard precheck, then act (promise log) or deny (assessment + appeal)."""
    store = LayerCStore(config, ensure_schema=True)
    task_row = store.fetch_task_for_source(registration_id, task_id)
    if not task_row:
        raise TaskRunError(
            f"No task {task_id!r} bound to registration {registration_id!r}"
        )

    extract_ref = str(task_row.get("extract_plan_ref", "") or "")
    task_name = str(task_row.get("task_name", "") or task_id)

    phases: list[str] = []
    sync_rows = resync_task_layer_a_from_plan(config, registration_id, extract_ref)
    phases.append("sync")

    server = mcp_server or PluginMcpServer(config)
    server.set_guard_source(registration_id)

    try:
        guard = server.invoke_guard_tool(guard_tool, subject_key)
    except GuardToolInvocationError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise TaskRunError(f"Guard precheck failed: {exc}") from exc
    phases.append("precheck")

    # Convention matches guard MCP integration tests: True => precheck passed (proceed).
    precheck_passed = guard.decision is True
    run_token = uuid.uuid4().hex[:12]
    promise_id = f"task-run-{task_id}-{run_token}"
    correlation_id = f"run-{task_id}-{run_token}"

    trace = guard.data_trace
    rule_id = str(trace.get("rule_id") or "unknown-rule")
    schema_hash = str(trace.get("schema_hash") or "unknown-schema")
    wm = trace.get("sync_watermark")
    sync_watermark = str(wm) if wm is not None else "unknown-watermark"
    layer_a_ref = f"layera://{registration_id}/subject/{subject_key}"

    if not precheck_passed:
        server.invoke_promise_tool(
            "promise.declare",
            {
                "creator_id": agent_id,
                "target_id": agent_id,
                "promise_id": promise_id,
                "promise_title": f"Task run blocked: {task_name}",
                "promise_state": "proposed",
            },
        )
        assessment_id = f"assess-deny-{run_token}"
        server.invoke_promise_tool(
            "promise.assess",
            {
                "assessor_id": agent_id,
                "assessor_name": agent_name,
                "assessment_id": assessment_id,
                "outcome": "deny",
                "notes": "Guard precheck did not pass; appeal via dashboard correlation.",
                "promise_id": promise_id,
                "correlation_id": correlation_id,
                "rule_id": rule_id,
                "schema_hash": schema_hash,
                "sync_watermark": sync_watermark,
                "layer_a_ref": layer_a_ref,
            },
        )
        phases.extend(["deny", "review"])
        return TaskRunResult(
            registration_id=registration_id,
            task_id=task_id,
            path="deny",
            phases_completed=tuple(phases),
            sync_rows_loaded=sync_rows,
            guard_tool=guard_tool,
            subject_key=subject_key,
            guard_decision=guard.decision,
            precheck_passed=False,
            promise_id=promise_id,
            assessment_id=assessment_id,
            correlation_id=correlation_id,
            rpa_steps=(),
            review={
                "dashboard_correlation_id": correlation_id,
                "appeal_hint": "Use promise.query with correlation_id for trace.",
            },
        )

    server.invoke_promise_tool(
        "promise.declare",
        {
            "creator_id": agent_id,
            "target_id": agent_id,
            "promise_id": promise_id,
            "promise_title": f"Task run approved: {task_name}",
            "promise_state": "accepted",
        },
    )
    server.invoke_promise_tool(
        "promise.chain",
        {
            "task_id": task_id,
            "task_name": task_name,
            "promise_id": promise_id,
        },
    )

    rpa_steps = (
        "extract_resynced",
        "guard_precheck_passed",
        "rpa_act_placeholder",
    )
    phases.append("act")

    assessment_id = f"assess-allow-{run_token}"
    server.invoke_promise_tool(
        "promise.assess",
        {
            "assessor_id": agent_id,
            "assessor_name": agent_name,
            "assessment_id": assessment_id,
            "outcome": "allow",
            "notes": "Guard precheck passed; RPA act phase logged (stub).",
            "promise_id": promise_id,
            "correlation_id": correlation_id,
        },
    )
    phases.append("review")

    return TaskRunResult(
        registration_id=registration_id,
        task_id=task_id,
        path="act",
        phases_completed=tuple(phases),
        sync_rows_loaded=sync_rows,
        guard_tool=guard_tool,
        subject_key=subject_key,
        guard_decision=guard.decision,
        precheck_passed=True,
        promise_id=promise_id,
        assessment_id=assessment_id,
        correlation_id=correlation_id,
        rpa_steps=rpa_steps,
        review={
            "promise_id": promise_id,
            "query_hint": "promise.query with promise_id for graph summary.",
        },
    )
