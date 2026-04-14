"""In-process Guard MCP tool registry with hot refresh (issue #57).

Maps Layer C rule rows to MCP tool names derived from TypeQL ``fun`` labels.
Refresh replaces the tool map atomically under a lock so the MCP host process
does not need restarting when rules or Layer A schema change.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass

from .config import AppConfig
from .layer_c_store import LayerCStore

_FUN_LABEL_PATTERN = re.compile(
    r"\bfun\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
    flags=re.MULTILINE,
)


@dataclass(frozen=True)
class GuardToolDescriptor:
    """One MCP-exposed guard tool (one TypeQL ``fun`` per rule)."""

    name: str
    rule_id: str
    rule_name: str
    registration_id: str


def extract_typeql_function_label(typeql_fun: str) -> str | None:
    """Return the first ``fun`` name in a schema fragment, or None."""
    match = _FUN_LABEL_PATTERN.search(typeql_fun.strip())
    return match.group(1) if match else None


class GuardMcpRegistry:
    """Thread-safe registry of guard tools, refreshed from Layer C rules."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._lock = threading.RLock()
        self._tools: dict[str, GuardToolDescriptor] = {}
        self._generation = 0
        self._last_registration_id: str | None = None

    @property
    def generation(self) -> int:
        with self._lock:
            return self._generation

    def refresh(self, registration_id: str) -> int:
        """Reload tools from Layer C for this source. Returns new generation."""
        store = LayerCStore(self._config, ensure_schema=True)
        rows = store.fetch_rules_for_source(registration_id)
        built: dict[str, GuardToolDescriptor] = {}
        for row in rows:
            status = str(row.get("rule_status", ""))
            if status == "archived":
                continue
            typeql = str(row.get("rule_typeql_fun", "") or "")
            label = extract_typeql_function_label(typeql)
            if not label:
                continue
            rule_id = str(row.get("rule_id", ""))
            rule_name = str(row.get("rule_name", ""))
            built[label] = GuardToolDescriptor(
                name=label,
                rule_id=rule_id,
                rule_name=rule_name,
                registration_id=registration_id,
            )
        with self._lock:
            self._tools = built
            self._generation += 1
            self._last_registration_id = registration_id
            return self._generation

    def list_tool_names(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._tools.keys()))

    def list_tools(self) -> tuple[GuardToolDescriptor, ...]:
        with self._lock:
            return tuple(sorted(self._tools.values(), key=lambda t: t.name))

    def get_tool(self, name: str) -> GuardToolDescriptor | None:
        with self._lock:
            return self._tools.get(name)
