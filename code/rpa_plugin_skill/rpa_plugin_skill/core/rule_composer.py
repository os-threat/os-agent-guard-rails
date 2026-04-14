from __future__ import annotations

import re
from dataclasses import dataclass


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


def compose_rule_preview(
    rule_id: str,
    rule_name: str,
    nl_text: str,
    target_entity: str = "gra_client",
    target_key_attribute: str = "gra_client_id",
    mode: str = "read-only",
) -> RuleComposerPreview:
    function_label = _function_label_from_rule_id(rule_id)
    horn = _build_horn_clause(rule_id, nl_text)
    diagram = _build_logic_diagram(rule_name, horn)
    define_query = _build_typeql_fun(function_label, target_entity, target_key_attribute)

    return RuleComposerPreview(
        nl_text=nl_text,
        logic_tab=LogicTab(horn_clause=horn, diagram_mermaid=diagram),
        typeql_tab=TypeQLTab(
            function_label=function_label,
            function_define_query=define_query,
            mode=mode,
        ),
    )


def _function_label_from_rule_id(rule_id: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", rule_id.strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    if not slug:
        slug = "rule"
    if slug[0].isdigit():
        slug = f"r_{slug}"
    return f"gr_guard_{slug}"


def _build_horn_clause(rule_id: str, nl_text: str) -> str:
    premise = _normalise_predicate_text(nl_text)
    return (
        f"deny({rule_id}) :- guard_input({rule_id}), {premise}. "
        f"allow({rule_id}) :- guard_input({rule_id}), not {premise}."
    )


def _normalise_predicate_text(nl_text: str) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", nl_text.lower())
    tail = "_".join(words[:6]) if words else "policy_condition"
    return f"condition_{tail}(X)"


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


def _build_typeql_fun(function_label: str, target_entity: str, target_key_attribute: str) -> str:
    return (
        "define\n"
        f"  fun {function_label}($subject_key: string) -> boolean:\n"
        "    match\n"
        f"      $subject isa {target_entity}, has {target_key_attribute} == $subject_key;\n"
        "    return check;\n"
    )
