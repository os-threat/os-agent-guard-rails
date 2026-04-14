from __future__ import annotations

import threading
from dataclasses import dataclass

from .config import AppConfig
from .guard_mcp_registry import GuardMcpRegistry


@dataclass(frozen=True)
class McpTool:
    namespace: str
    name: str
    description: str


class PluginMcpServer:
    """Long-lived MCP scaffold with Guard and Promise namespaces."""

    GUARD_NAMESPACE = "guard"
    PROMISE_NAMESPACE = "promise"

    def __init__(self, config: AppConfig, guard_registry: GuardMcpRegistry | None = None) -> None:
        self._config = config
        self._guard_registry = guard_registry or GuardMcpRegistry(config)
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
                description=f"Evaluate guard function for rule {tool.rule_id}.",
            )
            for tool in tools
        )

