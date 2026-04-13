from __future__ import annotations

import uuid
from dataclasses import replace

from typedb.driver import TransactionType

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.database_lifecycle import bootstrap_core_databases
from rpa_plugin_skill.core.layer_b_migrations import apply_layer_b_migrations
from rpa_plugin_skill.core.typedb_bootstrap import connect_with_retry


def _ephemeral_config() -> AppConfig:
    base = AppConfig.from_env()
    suffix = uuid.uuid4().hex[:8]
    return replace(
        base,
        layer_c_db=f"layer_c_contract_{suffix}",
        layer_b_db=f"layer_b_contract_{suffix}",
        layer_a_test_db=f"layer_a_contract_{suffix}",
    )


def _seed_contract_graph(config: AppConfig) -> None:
    driver = connect_with_retry(config)
    try:
        with driver.transaction(config.layer_b_db, TransactionType.WRITE) as tx:
            tx.query(
                '''insert
  $creator isa grb_agent,
    has grb_agent_id "agent-creator",
    has grb_agent_name "OpenClaw Planner";
  $target isa grb_agent,
    has grb_agent_id "agent-target",
    has grb_agent_name "System Target";

  $promise isa grb_promise,
    has grb_promise_id "promise-001",
    has grb_promise_title "Process appointment reminders",
    has grb_promise_state "accepted";

  $task isa grb_task,
    has grb_task_id "task-001",
    has grb_task_name "Reminder run";

  $assessment isa grb_assessment,
    has grb_assessment_id "assessment-001",
    has grb_assessment_outcome "allow",
    has grb_assessment_notes "Rule checks pass";

  $action isa grb_action,
    has grb_action_id "action-001",
    has grb_action_kind "guard_check",
    has grb_action_status "executed";

  $trace isa grb_data_trace,
    has grb_data_trace_id "trace-001",
    has grb_rule_id "MED-R01",
    has grb_schema_hash "schemahash-abc",
    has grb_sync_watermark "wm-123";

  $session isa grb_session,
    has grb_session_id "session-001",
    has grb_session_started_at 2026-04-01T10:00:00,
    has grb_session_ended_at 2026-04-01T10:05:00;

  (creator: $creator, target: $target, promise: $promise) isa grb_promise_binding;
  (task: $task, promise: $promise) isa grb_task_promise_binding;
  (assessor: $creator, assessment: $assessment, promise: $promise) isa grb_assessment_binding;
  (actor: $creator, action: $action, promise: $promise) isa grb_action_binding;
  (action: $action, data_trace: $trace) isa grb_action_data_trace_binding;
  (session: $session, agent: $creator) isa grb_session_participation;'''
            ).resolve()
            tx.commit()
    finally:
        driver.close()


def _assert_contract_queries(config: AppConfig) -> None:
    driver = connect_with_retry(config)
    try:
        with driver.transaction(config.layer_b_db, TransactionType.READ) as tx:
            answer = tx.query(
                '''match
  $promise isa grb_promise, has grb_promise_id "promise-001", has grb_promise_state $state;
  $task isa grb_task, has grb_task_id "task-001";
  (task: $task, promise: $promise) isa grb_task_promise_binding;
  $action isa grb_action, has grb_action_id "action-001", has grb_action_kind "guard_check";
  (actor: $agent, action: $action, promise: $promise) isa grb_action_binding;
  $trace isa grb_data_trace, has grb_data_trace_id "trace-001", has grb_rule_id $rule;
  (action: $action, data_trace: $trace) isa grb_action_data_trace_binding;
fetch {
  "promise_state": $state,
  "rule_id": $rule
};'''
            ).resolve()

            if not answer.is_concept_documents():
                raise RuntimeError("Expected concept documents from Layer B contract query")

            docs = list(answer.as_concept_documents())
            if not docs:
                raise RuntimeError("Layer B contract query returned no documents")

            rendered = str(docs[0])
            if "accepted" not in rendered or "MED-R01" not in rendered:
                raise RuntimeError("Layer B contract query missing expected values")

            count_answer = tx.query(
                '''match
  $a isa grb_action, has grb_action_kind "guard_check";
reduce $count = count;'''
            ).resolve()
            if not count_answer.is_concept_rows():
                raise RuntimeError("Expected concept rows from Layer B count query")
            rows = list(count_answer.as_concept_rows())
            if not rows:
                raise RuntimeError("Layer B count query returned no rows")
    finally:
        driver.close()


def _cleanup(config: AppConfig) -> None:
    try:
        driver = connect_with_retry(config)
    except Exception:
        return
    try:
        for db_name in (config.layer_b_db, config.layer_c_db):
            if driver.databases.contains(db_name):
                driver.databases.get(db_name).delete()
    finally:
        driver.close()


def main() -> int:
    # CI should provide a live TypeDB service; fail fast if unavailable.
    config = _ephemeral_config()
    bootstrap_core_databases(config)
    try:
        apply_layer_b_migrations(config)
        _seed_contract_graph(config)
        _assert_contract_queries(config)
    finally:
        _cleanup(config)

    print("[layer_b_contract] Contract seed/query checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

