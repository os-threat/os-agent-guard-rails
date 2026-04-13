from __future__ import annotations

import re
from dataclasses import dataclass

from typedb.driver import TransactionType

from .config import AppConfig
from .database_lifecycle import ensure_layer_a_database
from .sql_ddl_ingest import DDLModel, ForeignKeyDef, TableDef
from .typedb_bootstrap import connect_with_retry


@dataclass(frozen=True)
class LayerASchemaResult:
    registration_id: str
    layer_a_db: str
    query_kind: str


def generate_define_from_ddl(model: DDLModel, namespace: str = "gra") -> str:
    lines: list[str] = ["define"]

    for table in model.tables:
        entity_label = _entity_label(namespace, table.name)
        pk_mode = _pk_mode(table)

        for column in table.columns:
            attr_label = _attr_label(namespace, table.name, column.name)
            value_type = _map_sql_type_to_typeql(column.sql_type)
            lines.append(f"  attribute {attr_label}, value {value_type};")

        if pk_mode == "composite":
            lines.append(f"  attribute {entity_label}_composite_key, value string;")

    lines.append("")

    for table in model.tables:
        entity_label = _entity_label(namespace, table.name)
        pk_mode = _pk_mode(table)

        owns_parts: list[str] = []
        for column in table.columns:
            attr_label = _attr_label(namespace, table.name, column.name)
            if pk_mode == "single" and column.name == table.primary_key[0]:
                owns_parts.append(f"owns {attr_label} @key")
            else:
                owns_parts.append(f"owns {attr_label}")

        if pk_mode == "composite":
            owns_parts.append(f"owns {entity_label}_composite_key @key")

        if owns_parts:
            lines.append(f"  entity {entity_label},")
            for idx, part in enumerate(owns_parts):
                suffix = "," if idx < len(owns_parts) - 1 else ";"
                lines.append(f"    {part}{suffix}")
        else:
            lines.append(f"  entity {entity_label};")

        lines.append("")

    for table in model.tables:
        for idx, fk in enumerate(table.foreign_keys, start=1):
            relation_label = _fk_relation_label(namespace, table, fk, idx)
            from_role = f"{_safe_label(table.name)}_row"
            to_role = f"{_safe_label(fk.ref_table)}_row"
            from_entity = _entity_label(namespace, table.name)
            to_entity = _entity_label(namespace, fk.ref_table)

            lines.append(f"  relation {relation_label},")
            lines.append(f"    relates {from_role},")
            lines.append(f"    relates {to_role};")
            lines.append("")
            lines.append(f"  entity {from_entity},")
            lines.append(f"    plays {relation_label}:{from_role};")
            lines.append("")
            lines.append(f"  entity {to_entity},")
            lines.append(f"    plays {relation_label}:{to_role};")
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def apply_layer_a_schema(
    config: AppConfig,
    registration_id: str,
    define_query: str,
    redefine: bool = False,
) -> LayerASchemaResult:
    layer_a_db = ensure_layer_a_database(config, registration_id)
    query = define_query
    kind = "define"

    if redefine:
        kind = "redefine"
        query = _to_redefine_query(define_query)

    driver = connect_with_retry(config)
    try:
        with driver.transaction(layer_a_db, TransactionType.SCHEMA) as tx:
            tx.query(query).resolve()
            tx.commit()
    finally:
        driver.close()

    return LayerASchemaResult(
        registration_id=registration_id,
        layer_a_db=layer_a_db,
        query_kind=kind,
    )


def _to_redefine_query(query: str) -> str:
    return re.sub(r"^\s*define\b", "redefine", query, count=1, flags=re.IGNORECASE)


def _pk_mode(table: TableDef) -> str:
    if len(table.primary_key) == 1:
        return "single"
    if len(table.primary_key) > 1:
        return "composite"
    return "none"


def _entity_label(namespace: str, table_name: str) -> str:
    return f"{_safe_label(namespace)}_{_safe_label(table_name)}"


def _attr_label(namespace: str, table_name: str, column_name: str) -> str:
    return f"{_safe_label(namespace)}_{_safe_label(table_name)}_{_safe_label(column_name)}"


def _fk_relation_label(namespace: str, table: TableDef, fk: ForeignKeyDef, idx: int) -> str:
    left = _safe_label(table.name)
    right = _safe_label(fk.ref_table)
    return f"{_safe_label(namespace)}_{left}_to_{right}_fk_{idx}"


def _safe_label(name: str) -> str:
    label = re.sub(r"[^a-zA-Z0-9_]", "_", name.strip().lower())
    label = re.sub(r"_+", "_", label).strip("_")
    if not label:
        label = "x"
    if label[0].isdigit():
        label = f"x_{label}"
    return label


def _map_sql_type_to_typeql(sql_type: str) -> str:
    t = sql_type.strip().lower()
    if t.startswith(("int", "serial", "bigserial", "smallint", "bigint")):
        return "integer"
    if t.startswith(("numeric", "decimal")):
        return "decimal"
    if t.startswith(("double", "real", "float")):
        return "double"
    if t.startswith(("bool",)):
        return "boolean"
    if t.startswith(("timestamp",)):
        return "datetime"
    if t.startswith(("date",)):
        return "date"
    return "string"
