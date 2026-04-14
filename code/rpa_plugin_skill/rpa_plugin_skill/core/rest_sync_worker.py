from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from typedb.driver import TransactionType

from .config import AppConfig
from .database_lifecycle import ensure_layer_a_database
from .openapi_to_typeql import ExtractBundle
from .sql_to_typeql import _safe_label
from .typedb_bootstrap import connect_with_retry


@dataclass(frozen=True)
class RestSyncPlan:
    registration_id: str
    base_url: str
    bundle: ExtractBundle
    target_entity: str
    key_field: str = "id"
    response_records_key: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, str] = field(default_factory=dict)
    pagination_mode: str = "none"  # none | next_link
    max_pages: int = 1
    rate_limit_sleep_ms: int = 0


@dataclass(frozen=True)
class RestSyncResult:
    registration_id: str
    layer_a_db: str
    pages_fetched: int
    rows_synced: int


class RestSyncValidationError(ValueError):
    """Raised when REST sync plan or response payload is invalid."""


def sync_rest_bundle_to_layer_a(config: AppConfig, plan: RestSyncPlan) -> RestSyncResult:
    _validate_plan(plan)
    rows, pages = _fetch_rows(plan)
    layer_a_db = ensure_layer_a_database(config, plan.registration_id)
    driver = connect_with_retry(config)
    try:
        with driver.transaction(layer_a_db, TransactionType.WRITE) as tx:
            for row in rows:
                if row.get(plan.key_field) is None:
                    raise RestSyncValidationError(
                        f"Row missing key field '{plan.key_field}' required for idempotent put"
                    )
                query = _build_put_query(plan.target_entity, row)
                tx.query(query).resolve()
            tx.commit()
    finally:
        driver.close()
    return RestSyncResult(
        registration_id=plan.registration_id,
        layer_a_db=layer_a_db,
        pages_fetched=pages,
        rows_synced=len(rows),
    )


def _validate_plan(plan: RestSyncPlan) -> None:
    if not plan.registration_id.strip():
        raise RestSyncValidationError("registration_id is required")
    if not plan.base_url.strip():
        raise RestSyncValidationError("base_url is required")
    if not plan.target_entity.strip():
        raise RestSyncValidationError("target_entity is required")
    if plan.pagination_mode not in {"none", "next_link"}:
        raise RestSyncValidationError("pagination_mode must be one of: none, next_link")
    if plan.max_pages <= 0:
        raise RestSyncValidationError("max_pages must be > 0")
    if plan.rate_limit_sleep_ms < 0:
        raise RestSyncValidationError("rate_limit_sleep_ms must be >= 0")


def _fetch_rows(plan: RestSyncPlan) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    pages = 0
    next_url = _build_initial_url(plan)
    while next_url and pages < plan.max_pages:
        payload = _fetch_json(next_url, plan.bundle.method.upper(), plan.headers)
        page_rows = _extract_rows(payload, plan.response_records_key)
        rows.extend(page_rows)
        pages += 1
        if plan.pagination_mode == "next_link":
            next_url = _next_link(payload, plan.base_url)
        else:
            next_url = None
        if next_url and plan.rate_limit_sleep_ms > 0:
            time.sleep(plan.rate_limit_sleep_ms / 1000)
    return rows, pages


def _build_initial_url(plan: RestSyncPlan) -> str:
    base = plan.base_url.rstrip("/")
    path = plan.bundle.path
    if not path.startswith("/"):
        path = f"/{path}"
    url = f"{base}{path}"
    if plan.query_params:
        qs = urllib.parse.urlencode(plan.query_params)
        url = f"{url}?{qs}"
    return url


def _fetch_json(url: str, method: str, headers: dict[str, str]) -> Any:
    req = urllib.request.Request(url=url, method=method, headers=headers)
    with urllib.request.urlopen(req) as resp:  # nosec B310
        body = resp.read().decode("utf-8")
    return json.loads(body)


def _extract_rows(payload: Any, response_records_key: str | None) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        raise RestSyncValidationError("REST response must be an object or list")
    if response_records_key:
        value = payload.get(response_records_key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
        return []
    for key in ("data", "items", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return []


def _next_link(payload: Any, base_url: str) -> str | None:
    if not isinstance(payload, dict):
        return None
    raw = payload.get("next")
    if not isinstance(raw, str) or not raw.strip():
        return None
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    return urllib.parse.urljoin(base_url.rstrip("/") + "/", raw)


def _build_put_query(target_entity: str, row: dict[str, Any]) -> str:
    prefix = _safe_label(target_entity)
    owns_parts: list[str] = []
    for key, value in row.items():
        if value is None:
            continue
        attr = f"{prefix}_{_safe_label(key)}"
        owns_parts.append(f"has {attr} {_literal(value)}")
    if not owns_parts:
        raise RestSyncValidationError("REST row contained no non-null columns")
    attrs = ",\n    ".join(owns_parts)
    return f"""put
  $row isa {prefix},
    {attrs};"""


def _literal(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, Decimal):
        return f"{value}dec"
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'

