from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass


class RuleValidationError(ValueError):
    """Raised when natural-language rule text cannot be compiled safely."""


@dataclass(frozen=True)
class RuleAst:
    condition_text: str
    then_action: str
    else_action: str | None


@dataclass(frozen=True)
class RuleCodegenArtifacts:
    ast: RuleAst
    ast_ref: str
    horn_clause: str
    redefine_fun_query: str
    function_label: str


def compile_nl_rule(
    rule_id: str,
    nl_text: str,
    target_entity: str = "gra_client",
    target_key_attribute: str = "gra_client_id",
) -> RuleCodegenArtifacts:
    ast = parse_rule_ast(nl_text)
    function_label = function_label_from_rule_id(rule_id)

    horn_clause = build_horn_clause(function_label, ast)
    redefine_fun_query = build_redefine_fun_query(
        function_label=function_label,
        ast=ast,
        target_entity=target_entity,
        target_key_attribute=target_key_attribute,
    )
    validate_codegen_artifacts(horn_clause, redefine_fun_query)

    ast_doc = asdict(ast)
    ast_ref = f"ast-json://{json.dumps(ast_doc, separators=(',', ':'), ensure_ascii=True)}"

    return RuleCodegenArtifacts(
        ast=ast,
        ast_ref=ast_ref,
        horn_clause=horn_clause,
        redefine_fun_query=redefine_fun_query,
        function_label=function_label,
    )


def parse_rule_ast(nl_text: str) -> RuleAst:
    text = nl_text.strip()
    if not text:
        hint = (
            "Rule text is empty. Provide form: "
            "'If <condition> then <allow|deny> [else <allow|deny>]'."
        )
        raise RuleValidationError(
            hint
        )

    pattern = re.compile(
        r"^if\s+(?P<condition>.+?)\s+then\s+(?P<then>allow|deny)(?:\s+else\s+(?P<else>allow|deny))?\.?$",
        flags=re.IGNORECASE,
    )
    match = pattern.match(text)
    if not match:
        raise RuleValidationError(
            "Rule must match 'If <condition> then <allow|deny> [else <allow|deny>]'. "
            "Example: 'If concentration is high then deny else allow'."
        )

    condition_text = match.group("condition").strip()
    then_action = match.group("then").lower()
    else_action_raw = match.group("else")
    else_action = else_action_raw.lower() if else_action_raw else None

    if not condition_text:
        raise RuleValidationError("Rule condition is empty. Add text between 'If' and 'then'.")

    return RuleAst(
        condition_text=condition_text,
        then_action=then_action,
        else_action=else_action,
    )


def build_horn_clause(function_label: str, ast: RuleAst) -> str:
    predicate = predicate_from_condition(ast.condition_text)
    else_action = ast.else_action or ("allow" if ast.then_action == "deny" else "deny")

    first = f"{ast.then_action}({function_label}) :- {predicate}(X)."
    second = f"{else_action}({function_label}) :- not {predicate}(X)."
    return f"{first} {second}"


def build_redefine_fun_query(
    function_label: str,
    ast: RuleAst,
    target_entity: str,
    target_key_attribute: str,
) -> str:
    predicate = predicate_from_condition(ast.condition_text)
    expected = "true" if ast.then_action == "allow" else "false"

    return (
        "redefine\n"
        f"  fun {function_label}($subject_key: string) -> boolean:\n"
        "    match\n"
        f"      $subject isa {target_entity}, has {target_key_attribute} == $subject_key;\n"
        f"      $condition_label == \"{predicate}\";\n"
        f"    return {expected};\n"
    )


def validate_codegen_artifacts(horn_clause: str, redefine_fun_query: str) -> None:
    if not horn_clause.strip().endswith("."):
        raise RuleValidationError("Horn clause must terminate with a period.")

    lines = [line.rstrip() for line in redefine_fun_query.splitlines() if line.strip()]
    if not lines or lines[0] != "redefine":
        raise RuleValidationError("TypeQL codegen must start with 'redefine'.")

    fun_line = next((line for line in lines if line.strip().startswith("fun ")), None)
    if not fun_line:
        raise RuleValidationError("TypeQL codegen missing function signature line.")

    for line in lines[1:]:
        stripped = line.strip()
        if stripped.endswith(":"):
            continue
        if stripped in {"match"}:
            continue
        if not stripped.endswith(";"):
            raise RuleValidationError(
                f"TypeQL fragment line must end with semicolon: '{stripped}'"
            )


def function_label_from_rule_id(rule_id: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", rule_id.strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    if not slug:
        slug = "rule"
    if slug[0].isdigit():
        slug = f"r_{slug}"
    return f"gr_guard_{slug}"


def predicate_from_condition(condition_text: str) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", condition_text.lower())
    suffix = "_".join(words[:8]) if words else "condition"
    return f"cond_{suffix}"
