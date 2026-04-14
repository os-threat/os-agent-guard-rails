from __future__ import annotations

from dataclasses import dataclass

from .nl_rule_codegen import compile_nl_rule


@dataclass(frozen=True)
class LogicTab:
    horn_clause: str
    diagram_mermaid: str


@dataclass(frozen=True)
class TypeQLTab:
    function_label: str
    function_define_query: str
    mode: str


@dataclass(frozen=True)
class RuleComposerPreview:
    nl_text: str
    logic_tab: LogicTab
    typeql_tab: TypeQLTab
    ast_ref: str


def compose_rule_preview(
    rule_id: str,
    rule_name: str,
    nl_text: str,
    target_entity: str = "gra_client",
    target_key_attribute: str = "gra_client_id",
    mode: str = "read-only",
) -> RuleComposerPreview:
    artifacts = compile_nl_rule(
        rule_id=rule_id,
        nl_text=nl_text,
        target_entity=target_entity,
        target_key_attribute=target_key_attribute,
    )
    diagram = _build_logic_diagram(rule_name, artifacts.horn_clause)

    return RuleComposerPreview(
        nl_text=nl_text,
        logic_tab=LogicTab(horn_clause=artifacts.horn_clause, diagram_mermaid=diagram),
        typeql_tab=TypeQLTab(
            function_label=artifacts.function_label,
            function_define_query=artifacts.redefine_fun_query,
            mode=mode,
        ),
        ast_ref=artifacts.ast_ref,
    )


def _build_logic_diagram(rule_name: str, horn_clause: str) -> str:
    safe_name = rule_name.replace('"', "'")
    safe_horn = horn_clause.replace('"', "'")
    return (
        "flowchart LR\n"
        f"  NL[\"{safe_name}: NL Rule\"] --> H[\"Horn IF/THEN/ELSE\"]\n"
        f"  H --> C{{\"{safe_horn}\"}}\n"
        "  C -->|true| D[DENY]\n"
        "  C -->|false| A[ALLOW]\n"
    )
