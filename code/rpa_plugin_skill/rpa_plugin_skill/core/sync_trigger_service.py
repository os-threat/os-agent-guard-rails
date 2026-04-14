from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass

from .config import AppConfig
from .layer_c_store import LayerCStore
from .rest_sync_worker import RestSyncPlan, sync_rest_bundle_to_layer_a
from .sql_sync_worker import SqlSyncPlan, sync_sql_rows_to_layer_a


@dataclass(frozen=True)
class SyncStatus:
    registration_id: str
    last_sync_time: str | None
    last_sync_error: str | None
    last_sync_rows: str | None
    last_sync_trigger: str | None


def trigger_post_registration_sync(
    config: AppConfig, registration_id: str, source_kind: str
) -> SyncStatus:
    store = LayerCStore(config, ensure_schema=True)
    _set(store, registration_id, "last_sync_trigger", f"post_registration:{source_kind}")
    _set(store, registration_id, "last_sync_error", "")
    _set(store, registration_id, "last_sync_rows", "0")
    _set(store, registration_id, "last_sync_time", _utc_now())
    return get_sync_status(config, registration_id)


def trigger_post_task_finalize_sync(
    config: AppConfig, registration_id: str, task_id: str
) -> SyncStatus:
    store = LayerCStore(config, ensure_schema=True)
    _set(store, registration_id, "last_sync_trigger", f"post_task_finalize:{task_id}")
    _set(store, registration_id, "last_sync_time", _utc_now())
    return get_sync_status(config, registration_id)


def trigger_manual_sql_sync(config: AppConfig, plan: SqlSyncPlan) -> SyncStatus:
    store = LayerCStore(config, ensure_schema=True)
    _set(store, plan.registration_id, "last_sync_trigger", "manual_sql_refresh")
    try:
        result = sync_sql_rows_to_layer_a(config, plan)
    except Exception as exc:  # noqa: BLE001
        _set(store, plan.registration_id, "last_sync_error", str(exc))
        _set(store, plan.registration_id, "last_sync_time", _utc_now())
        raise
    _set(store, plan.registration_id, "last_sync_error", "")
    _set(store, plan.registration_id, "last_sync_rows", str(result.rows_synced))
    _set(store, plan.registration_id, "last_sync_time", _utc_now())
    return get_sync_status(config, plan.registration_id)


def trigger_manual_rest_sync(config: AppConfig, plan: RestSyncPlan) -> SyncStatus:
    store = LayerCStore(config, ensure_schema=True)
    _set(store, plan.registration_id, "last_sync_trigger", "manual_rest_refresh")
    try:
        result = sync_rest_bundle_to_layer_a(config, plan)
    except Exception as exc:  # noqa: BLE001
        _set(store, plan.registration_id, "last_sync_error", str(exc))
        _set(store, plan.registration_id, "last_sync_time", _utc_now())
        raise
    _set(store, plan.registration_id, "last_sync_error", "")
    _set(store, plan.registration_id, "last_sync_rows", str(result.rows_synced))
    _set(store, plan.registration_id, "last_sync_time", _utc_now())
    return get_sync_status(config, plan.registration_id)


def get_sync_status(config: AppConfig, registration_id: str) -> SyncStatus:
    store = LayerCStore(config, ensure_schema=True)
    return SyncStatus(
        registration_id=registration_id,
        last_sync_time=_get(store, registration_id, "last_sync_time"),
        last_sync_error=_get(store, registration_id, "last_sync_error"),
        last_sync_rows=_get(store, registration_id, "last_sync_rows"),
        last_sync_trigger=_get(store, registration_id, "last_sync_trigger"),
    )


def sync_status_as_dict(config: AppConfig, registration_id: str) -> dict:
    return asdict(get_sync_status(config, registration_id))


def _set(store: LayerCStore, registration_id: str, field: str, value: str) -> None:
    store.upsert_setting(_key(registration_id, field), value)


def _get(store: LayerCStore, registration_id: str, field: str) -> str | None:
    return store.fetch_setting(_key(registration_id, field))


def _key(registration_id: str, field: str) -> str:
    return f"sync:{registration_id}:{field}"


def _utc_now() -> str:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    return now.isoformat().replace("+00:00", "Z")
