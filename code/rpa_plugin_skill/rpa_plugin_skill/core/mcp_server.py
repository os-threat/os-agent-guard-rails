from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass

from typedb.driver import TransactionType

from .config import AppConfig
from .database_lifecycle import layer_a_db_name
from .guard_mcp_registry import GuardMcpRegistry
from .layer_c_store import LayerCStore
from .promise_mcp_service import PromiseMcpService, PromiseToolResult
from .typedb_bootstrap import connect_with_retry


@dataclass(frozen=True)
class McpTool:
    namespace: str
    name: str
    description: str


@dataclass(frozen=True)
class GuardInvocationResult:
    tool_name: str
    registration_id: str
    subject_key: str
    decision: bool | None
    data_trace: dict[str, str | None]


class GuardToolInvocationError(ValueError):
    """Raised when a guard tool cannot be invoked safely."""


class PluginMcpServer:
    """Long-lived MCP scaffold with Guard and Promise namespaces."""

    GUARD_NAMESPACE = "guard"
    PROMISE_NAMESPACE = "promise"

    def __init__(self, config: AppConfig, guard_registry: GuardMcpRegistry | None = None) -> None:
        self._config = config
        self._guard_registry = guard_registry or GuardMcpRegistry(config)
        self._promise_service = PromiseMcpService(config)
        self._lock = threading.RLock()
        self._active_guard_source: str | None = None
        self._promise_tools: tuple[McpTool, ...] = (
            McpTool(
                namespace=self.PROMISE_NAMESPACE,
                name="promise.declare",
                description="Declare a promise in Layer B graph.",
            ),
            McpTool(
                namespace=self.PROMISE_NAMESPACE,
                name="promise.chain",
                description="Link promises in Layer B graph.",
            ),
            McpTool(
                namespace=self.PROMISE_NAMESPACE,
                name="promise.assess",
                description="Record promise assessment outcome.",
            ),
            McpTool(
                namespace=self.PROMISE_NAMESPACE,
                name="promise.query",
                description="Query promise graph status and lineage.",
            ),
        )

    def set_guard_source(self, registration_id: str) -> int:
        with self._lock:
            self._active_guard_source = registration_id
            return self._guard_registry.refresh(registration_id)

    def list_namespaces(self) -> tuple[str, ...]:
        return (self.GUARD_NAMESPACE, self.PROMISE_NAMESPACE)

    def list_tools(self, namespace: str) -> tuple[McpTool, ...]:
        if namespace == self.PROMISE_NAMESPACE:
            return self._promise_tools
        if namespace == self.GUARD_NAMESPACE:
            return self._guard_tools()
        return ()

    def invoke_guard_tool(self, tool_name: str, subject_key: str) -> GuardInvocationResult:
        with self._lock:
            source = self._active_guard_source
        if not source:
            raise GuardToolInvocationError(
                "Guard source is not set. Call set_guard_source(registration_id) first."
            )

        bare_tool_name = tool_name.removeprefix("guard.")
        descriptor = self._guard_registry.get_tool(bare_tool_name)
        if not descriptor:
            raise GuardToolInvocationError(f"Unknown guard tool: {tool_name}")

        decision = self._execute_guard_fun(source, bare_tool_name, subject_key)
        trace = self._data_trace_for_source(source, descriptor.rule_id)
        return GuardInvocationResult(
            tool_name=tool_name,
            registration_id=source,
            subject_key=subject_key,
            decision=decision,
            data_trace=trace,
        )

    def introspect_guard_tool(self, tool_name: str) -> dict[str, str | None]:
        with self._lock:
            source = self._active_guard_source
        if not source:
            raise GuardToolInvocationError(
                "Guard source is not set. Call set_guard_source(registration_id) first."
            )

        bare_tool_name = tool_name.removeprefix("guard.")
        descriptor = self._guard_registry.get_tool(bare_tool_name)
        if not descriptor:
            raise GuardToolInvocationError(f"Unknown guard tool: {tool_name}")
        return self._data_trace_for_source(source, descriptor.rule_id)

    def invoke_promise_tool(self, tool_name: str, payload: dict) -> PromiseToolResult:
        return self._promise_service.invoke(tool_name, payload)

    def _guard_tools(self) -> tuple[McpTool, ...]:
        with self._lock:
            source = self._active_guard_source
        if source:
            self._guard_registry.refresh(source)
        tools = self._guard_registry.list_tools()
        return tuple(
            McpTool(
                namespace=self.GUARD_NAMESPACE,
                name=f"guard.{tool.name}",
                description=(
                    f"Evaluate guard function for rule {tool.rule_id}. "
                    "Includes data-trace: rule_id, schema_hash, sync_watermark."
                ),
            )
            for tool in tools
        )

    def _execute_guard_fun(
        self,
        registration_id: str,
        fun_label: str,
        subject_key: str,
    ) -> bool | None:
        layer_a_db = layer_a_db_name(self._config, registration_id)
        escaped = subject_key.replace("\\", "\\\\").replace('"', '\\"')
        query = f"""match
  let $decision in {fun_label}("{escaped}");
fetch {{
  "decision": $decision
}};"""
        driver = connect_with_retry(self._config)
        try:
            with driver.transaction(layer_a_db, TransactionType.READ) as tx:
                answer = tx.query(query).resolve()
                if not answer.is_concept_documents():
                    return None
                docs = list(answer.as_concept_documents())
                if not docs:
                    return None
                raw = docs[0].get("decision")
                if isinstance(raw, bool):
                    return raw
                rendered = str(raw).strip().lower()
                if rendered in {"true", "false"}:
                    return rendered == "true"
                return None
        except Exception as exc:  # noqa: BLE001
            msg = (
                f"Failed to invoke guard function '{fun_label}' "
                f"on source '{registration_id}': {exc}"
            )
            raise GuardToolInvocationError(
                msg
            ) from exc
        finally:
            driver.close()

    def _data_trace_for_source(self, registration_id: str, rule_id: str) -> dict[str, str | None]:
        layer_a_db = layer_a_db_name(self._config, registration_id)
        driver = connect_with_retry(self._config)
        try:
            schema = ""
            if driver.databases.contains(layer_a_db):
                schema = driver.databases.get(layer_a_db).schema()
        finally:
            driver.close()

        schema_hash = hashlib.sha256(schema.encode("utf-8")).hexdigest() if schema else None
        store = LayerCStore(self._config, ensure_schema=True)
        watermark = store.fetch_setting(f"sync:{registration_id}:last_sync_time")
        return {
            "rule_id": rule_id,
            "schema_hash": schema_hash,
            "sync_watermark": watermark,
        }

