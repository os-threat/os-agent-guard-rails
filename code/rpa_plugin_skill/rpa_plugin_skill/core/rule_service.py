from __future__ import annotations

from dataclasses import dataclass

from typedb.driver import TransactionType

from .config import AppConfig
from .database_lifecycle import layer_a_db_name
from .layer_c_store import LayerCStore
from .nl_rule_codegen import compile_nl_rule
from .typedb_bootstrap import connect_with_retry


@dataclass(frozen=True)
class RulePreview:
    registration_id: str
    rule_id: str
    rule_name: str
    rule_status: str
    layer_a_db: str


def upsert_rule_for_source(
    config: AppConfig,
    registration_id: str,
    rule_id: str,
    rule_name: str,
    nl_text: str,
    horn_text: str,
    typeql_fun: str,
    ast_ref: str,
    status: str = "draft",
    apply_layer_a_logic: bool = True,
) -> RulePreview:
    if apply_layer_a_logic and typeql_fun.strip():
        _apply_schema_query(config, registration_id, typeql_fun)

    store = LayerCStore(config, ensure_schema=True)
    store.upsert_rule(
        registration_id=registration_id,
        rule_id=rule_id,
        rule_name=rule_name,
        nl_text=nl_text,
        horn_text=horn_text,
        typeql_fun=typeql_fun,
        ast_ref=ast_ref,
        status=status,
    )

    return RulePreview(
        registration_id=registration_id,
        rule_id=rule_id,
        rule_name=rule_name,
        rule_status=status,
        layer_a_db=layer_a_db_name(config, registration_id),
    )


def upsert_rule_from_nl_for_source(
    config: AppConfig,
    registration_id: str,
    rule_id: str,
    rule_name: str,
    nl_text: str,
    status: str = "draft",
) -> RulePreview:
    artifacts = compile_nl_rule(rule_id=rule_id, nl_text=nl_text)
    return upsert_rule_for_source(
        config=config,
        registration_id=registration_id,
        rule_id=rule_id,
        rule_name=rule_name,
        nl_text=nl_text,
        horn_text=artifacts.horn_clause,
        typeql_fun=artifacts.redefine_fun_query,
        ast_ref=artifacts.ast_ref,
        status=status,
        apply_layer_a_logic=True,
    )


def list_rules_for_source(config: AppConfig, registration_id: str) -> list[dict]:
    store = LayerCStore(config, ensure_schema=True)
    return store.fetch_rules_for_source(registration_id)


def archive_rule_for_source(config: AppConfig, registration_id: str, rule_id: str) -> None:
    _ = registration_id
    store = LayerCStore(config, ensure_schema=True)
    store.set_rule_status(rule_id=rule_id, status="archived")


def delete_rule_for_source(
    config: AppConfig,
    registration_id: str,
    rule_id: str,
    undefine_query: str | None = None,
) -> None:
    if undefine_query and undefine_query.strip():
        _apply_schema_query(config, registration_id, undefine_query)

    store = LayerCStore(config, ensure_schema=True)
    store.delete_rule(registration_id=registration_id, rule_id=rule_id)


def _apply_schema_query(config: AppConfig, registration_id: str, schema_query: str) -> None:
    db_name = layer_a_db_name(config, registration_id)
    driver = connect_with_retry(config)
    try:
        with driver.transaction(db_name, TransactionType.SCHEMA) as tx:
            tx.query(schema_query).resolve()
            tx.commit()
    finally:
        driver.close()
