from __future__ import annotations

import unittest

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.guard_mcp_registry import GuardToolDescriptor
from rpa_plugin_skill.core.mcp_server import PluginMcpServer


class _FakeGuardRegistry:
    def __init__(self) -> None:
        self.refresh_calls: list[str] = []
        self._tools: tuple[GuardToolDescriptor, ...] = ()

    def refresh(self, registration_id: str) -> int:
        self.refresh_calls.append(registration_id)
        self._tools = (
            GuardToolDescriptor(
                name="gr_guard_fp_r01",
                rule_id="FP-R01",
                rule_name="Diversification threshold",
                registration_id=registration_id,
            ),
        )
        return len(self.refresh_calls)

    def list_tools(self) -> tuple[GuardToolDescriptor, ...]:
        return self._tools

    def get_tool(self, name: str) -> GuardToolDescriptor | None:
        for tool in self._tools:
            if tool.name == name:
                return tool
        return None


class McpServerScaffoldTests(unittest.TestCase):
    def test_lists_guard_and_promise_namespaces(self) -> None:
        cfg = AppConfig.from_env()
        fake_registry = _FakeGuardRegistry()
        server = PluginMcpServer(cfg, guard_registry=fake_registry)  # type: ignore[arg-type]

        namespaces = server.list_namespaces()
        self.assertEqual(namespaces, ("guard", "promise"))

    def test_lists_promise_namespace_tools_without_guard_refresh(self) -> None:
        cfg = AppConfig.from_env()
        fake_registry = _FakeGuardRegistry()
        server = PluginMcpServer(cfg, guard_registry=fake_registry)  # type: ignore[arg-type]

        tools = server.list_tools("promise")
        names = [tool.name for tool in tools]
        self.assertIn("promise.declare", names)
        self.assertIn("promise.query", names)
        self.assertEqual(fake_registry.refresh_calls, [])

    def test_lists_guard_tools_after_setting_guard_source(self) -> None:
        cfg = AppConfig.from_env()
        fake_registry = _FakeGuardRegistry()
        server = PluginMcpServer(cfg, guard_registry=fake_registry)  # type: ignore[arg-type]

        generation = server.set_guard_source("sql-medical-alpha")
        self.assertEqual(generation, 1)

        tools = server.list_tools("guard")
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0].name, "guard.gr_guard_fp_r01")

    def test_guard_contract_list_matches_fun_set_after_reload(self) -> None:
        cfg = AppConfig.from_env()
        fake_registry = _FakeGuardRegistry()
        server = PluginMcpServer(cfg, guard_registry=fake_registry)  # type: ignore[arg-type]
        server.set_guard_source("sql-medical-alpha")

        names = {tool.name for tool in server.list_tools("guard")}
        self.assertEqual(names, {"guard.gr_guard_fp_r01"})


if __name__ == "__main__":
    unittest.main()
