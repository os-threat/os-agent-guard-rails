from __future__ import annotations

import datetime as dt
import decimal
import re
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg.rows import dict_row
from typedb.driver import TransactionType

from .config import AppConfig
from .database_lifecycle import ensure_layer_a_database
from .sql_to_typeql import _safe_label
from .typedb_bootstrap import connect_with_retry


@dataclass(frozen=True)
class SqlSyncPlan:
    registration_id: str
    sql_dsn: str
    sql_query: str
    source_table: str
    key_column: str = "id"
    watermark_column: str | None = None
    watermark_gt: Any | None = None
    limit: int | None = None


@dataclass(frozen=True)
class SqlSyncResult:
    registration_id: str
    layer_a_db: str
    rows_synced: int
    watermark_max: Any | None


class SqlSyncValidationError(ValueError):
    """Raised when a SQL sync plan is missing required mapping fields."""


def sync_sql_rows_to_layer_a(
    config: AppConfig,
    plan: SqlSyncPlan,
    namespace: str = "gra",
) -> SqlSyncResult:
    _validate_plan(plan)
    rows = _fetch_sql_rows(plan)
    layer_a_db = ensure_layer_a_database(config, plan.registration_id)

    entity_label = f"{_safe_label(namespace)}_{_safe_label(plan.source_table)}"
    driver = connect_with_retry(config)
    try:
        with driver.transaction(layer_a_db, TransactionType.WRITE) as tx:
            for row in rows:
                if row.get(plan.key_column) is None:
                    raise SqlSyncValidationError(
                        f"Row missing key column '{plan.key_column}' required for idempotent put"
                    )
                query = _build_put_query(entity_label, plan.source_table, row, namespace)
                tx.query(query).resolve()
            tx.commit()
    finally:
        driver.close()

    watermark_max = None
    if plan.watermark_column and rows:
        watermark_max = rows[-1].get(plan.watermark_column)

    return SqlSyncResult(
        registration_id=plan.registration_id,
        layer_a_db=layer_a_db,
        rows_synced=len(rows),
        watermark_max=watermark_max,
    )


def _validate_plan(plan: SqlSyncPlan) -> None:
    if not plan.registration_id.strip():
        raise SqlSyncValidationError("registration_id is required")
    if not plan.sql_dsn.strip():
        raise SqlSyncValidationError("sql_dsn is required")
    if not plan.sql_query.strip():
        raise SqlSyncValidationError("sql_query is required")
    if not plan.source_table.strip():
        raise SqlSyncValidationError("source_table is required")
    if not plan.key_column.strip():
        raise SqlSyncValidationError("key_column is required")


def _fetch_sql_rows(plan: SqlSyncPlan) -> list[dict[str, Any]]:
    query, params = _build_source_query(plan)
    with psycopg.connect(plan.sql_dsn, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            fetched = cur.fetchall()
    return [dict(row) for row in fetched]


def _build_source_query(plan: SqlSyncPlan) -> tuple[str, tuple[Any, ...]]:
    query = plan.sql_query.strip().rstrip(";")
    params: list[Any] = []

    if plan.watermark_column and plan.watermark_gt is not None:
        if not _is_simple_identifier(plan.watermark_column):
            raise SqlSyncValidationError(
                "watermark_column must be a simple SQL identifier"
            )
        wrapped = (
            f"SELECT * FROM ({query}) AS src "
            f"WHERE {plan.watermark_column} > %s "
            f"ORDER BY {plan.watermark_column} ASC"
        )
        query = wrapped
        params.append(plan.watermark_gt)

    if plan.limit is not None:
        if plan.limit <= 0:
            raise SqlSyncValidationError("limit must be > 0")
        query = f"{query} LIMIT {plan.limit}"

    return query, tuple(params)


def _is_simple_identifier(value: str) -> bool:
    return bool(re.match(r"^[a-zA-Z_]\w*$", value))


def _build_put_query(
    entity_label: str,
    source_table: str,
    row: dict[str, Any],
    namespace: str,
) -> str:
    owns_parts: list[str] = []
    for column, value in row.items():
        if value is None:
            continue
        attr = f"{_safe_label(namespace)}_{_safe_label(source_table)}_{_safe_label(column)}"
        literal = _to_typeql_literal(value)
        owns_parts.append(f"has {attr} {literal}")

    if not owns_parts:
        raise SqlSyncValidationError("Row has no non-null columns to map into Layer A")

    attrs = ",\n    ".join(owns_parts)
    return f"""put
  $row isa {entity_label},
    {attrs};"""


def _to_typeql_literal(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, decimal.Decimal):
        return f"{value}dec"
    if isinstance(value, dt.datetime):
        return value.isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()

    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
