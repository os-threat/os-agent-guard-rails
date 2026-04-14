from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typedb.driver import TransactionType

from .config import AppConfig
from .typedb_bootstrap import connect_with_retry


@dataclass(frozen=True)
class PromiseToolResult:
    tool_name: str
    payload: dict[str, Any]


class PromiseToolInputError(ValueError):
    """Raised when required payload fields are missing for promise tools."""


class PromiseMcpService:
    """Static promise MCP tool surface backed by dynamic Layer B data."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def invoke(self, tool_name: str, payload: dict[str, Any]) -> PromiseToolResult:
        if tool_name == "promise.declare":
            result = self._declare(payload)
        elif tool_name == "promise.chain":
            result = self._chain(payload)
        elif tool_name == "promise.assess":
            result = self._assess(payload)
        elif tool_name == "promise.query":
            result = self._query(payload)
        else:
            raise PromiseToolInputError(f"Unsupported promise tool: {tool_name}")
        return PromiseToolResult(tool_name=tool_name, payload=result)

    def _declare(self, payload: dict[str, Any]) -> dict[str, Any]:
        creator_id = _required(payload, "creator_id")
        target_id = _required(payload, "target_id")
        promise_id = _required(payload, "promise_id")
        promise_title = _required(payload, "promise_title")
        promise_state = str(payload.get("promise_state", "proposed"))
        creator_name = str(payload.get("creator_name", creator_id))
        target_name = str(payload.get("target_name", target_id))

        driver = connect_with_retry(self._config)
        try:
            with driver.transaction(self._config.layer_b_db, TransactionType.WRITE) as tx:
                tx.query(
                    f"""put
  $creator isa grb_agent,
    has grb_agent_id "{creator_id}",
    has grb_agent_name "{creator_name}";
  $target isa grb_agent,
    has grb_agent_id "{target_id}",
    has grb_agent_name "{target_name}";
  $promise isa grb_promise,
    has grb_promise_id "{promise_id}",
    has grb_promise_title "{promise_title}",
    has grb_promise_state "{promise_state}";"""
                ).resolve()
                tx.query(
                    f"""match
  $creator isa grb_agent, has grb_agent_id "{creator_id}";
  $target isa grb_agent, has grb_agent_id "{target_id}";
  $promise isa grb_promise, has grb_promise_id "{promise_id}";
put
  (creator: $creator, target: $target, promise: $promise) isa grb_promise_binding;"""
                ).resolve()
                tx.commit()
        finally:
            driver.close()

        return {
            "promise_id": promise_id,
            "promise_state": promise_state,
            "creator_id": creator_id,
            "target_id": target_id,
        }

    def _chain(self, payload: dict[str, Any]) -> dict[str, Any]:
        task_id = _required(payload, "task_id")
        task_name = _required(payload, "task_name")
        promise_id = _required(payload, "promise_id")

        driver = connect_with_retry(self._config)
        try:
            with driver.transaction(self._config.layer_b_db, TransactionType.WRITE) as tx:
                tx.query(
                    f"""put
  $task isa grb_task,
    has grb_task_id "{task_id}",
    has grb_task_name "{task_name}";
  $promise isa grb_promise, has grb_promise_id "{promise_id}";"""
                ).resolve()
                tx.query(
                    f"""match
  $task isa grb_task, has grb_task_id "{task_id}";
  $promise isa grb_promise, has grb_promise_id "{promise_id}";
put
  (task: $task, promise: $promise) isa grb_task_promise_binding;"""
                ).resolve()
                tx.commit()
        finally:
            driver.close()

        return {"task_id": task_id, "promise_id": promise_id}

    def _assess(self, payload: dict[str, Any]) -> dict[str, Any]:
        assessor_id = _required(payload, "assessor_id")
        assessment_id = _required(payload, "assessment_id")
        outcome = _required(payload, "outcome")
        promise_id = _required(payload, "promise_id")
        notes = str(payload.get("notes", ""))
        assessor_name = str(payload.get("assessor_name", assessor_id))

        driver = connect_with_retry(self._config)
        try:
            with driver.transaction(self._config.layer_b_db, TransactionType.WRITE) as tx:
                tx.query(
                    f"""put
  $assessor isa grb_agent,
    has grb_agent_id "{assessor_id}",
    has grb_agent_name "{assessor_name}";
  $assessment isa grb_assessment,
    has grb_assessment_id "{assessment_id}",
    has grb_assessment_outcome "{outcome}",
    has grb_assessment_notes "{notes}";
  $promise isa grb_promise, has grb_promise_id "{promise_id}";"""
                ).resolve()
                tx.query(
                    f"""match
  $assessor isa grb_agent, has grb_agent_id "{assessor_id}";
  $assessment isa grb_assessment, has grb_assessment_id "{assessment_id}";
  $promise isa grb_promise, has grb_promise_id "{promise_id}";
put
  (assessor: $assessor, assessment: $assessment, promise: $promise) isa grb_assessment_binding;"""
                ).resolve()
                tx.commit()
        finally:
            driver.close()

        return {
            "assessment_id": assessment_id,
            "promise_id": promise_id,
            "outcome": outcome,
        }

    def _query(self, payload: dict[str, Any]) -> dict[str, Any]:
        promise_id = _required(payload, "promise_id")
        driver = connect_with_retry(self._config)
        try:
            with driver.transaction(self._config.layer_b_db, TransactionType.READ) as tx:
                details = tx.query(
                    f"""match
  $promise isa grb_promise,
    has grb_promise_id "{promise_id}",
    has grb_promise_title $title,
    has grb_promise_state $state;
fetch {{
  "promise_id": "{promise_id}",
  "promise_title": $title,
  "promise_state": $state
}};"""
                ).resolve()
                if not details.is_concept_documents():
                    raise PromiseToolInputError(
                        f"Promise not found for promise_id={promise_id}"
                    )
                docs = list(details.as_concept_documents())
                if not docs:
                    raise PromiseToolInputError(
                        f"Promise not found for promise_id={promise_id}"
                    )
                summary = dict(docs[0])

                assessments = tx.query(
                    f"""match
  $promise isa grb_promise, has grb_promise_id "{promise_id}";
  (promise: $promise, assessment: $a) isa grb_assessment_binding;
fetch {{
  "assessment": $a
}};"""
                ).resolve()
                actions = tx.query(
                    f"""match
  $promise isa grb_promise, has grb_promise_id "{promise_id}";
  (promise: $promise, action: $a) isa grb_action_binding;
fetch {{
  "action": $a
}};"""
                ).resolve()
        finally:
            driver.close()

        assessment_count = (
            len(list(assessments.as_concept_documents()))
            if assessments.is_concept_documents()
            else 0
        )
        action_count = (
            len(list(actions.as_concept_documents()))
            if actions.is_concept_documents()
            else 0
        )
        return {
            "promise_id": summary.get("promise_id"),
            "promise_title": summary.get("promise_title"),
            "promise_state": summary.get("promise_state"),
            "assessment_count": assessment_count,
            "action_count": action_count,
        }


def _required(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if value is None:
        raise PromiseToolInputError(f"Missing required payload field: {key}")
    text = str(value).strip()
    if not text:
        raise PromiseToolInputError(f"Missing required payload field: {key}")
    return text
