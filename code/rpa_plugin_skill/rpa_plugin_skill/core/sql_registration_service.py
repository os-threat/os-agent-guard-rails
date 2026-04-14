from __future__ import annotations

import re
from dataclasses import dataclass

from .config import AppConfig
from .database_lifecycle import layer_a_db_name
from .layer_c_store import LayerCStore, RegisteredSourceInput
from .sql_ddl_ingest import load_ddl_text, parse_postgres_ddl
from .sql_to_typeql import apply_layer_a_schema, generate_define_from_ddl
from .sync_trigger_service import trigger_post_registration_sync


@dataclass(frozen=True)
class RegistrationPreview:
    registration_id: str
    source_name: str
    source_kind: str
    source_url: str
    layer_a_db: str
    tables: tuple[str, ...]


def _slugify(value: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "source"


def register_sql_source(
    config: AppConfig,
    source_name: str,
    ddl_source: str,
    source_url: str,
    registration_id: str | None = None,
) -> RegistrationPreview:
    reg_id = registration_id or f"sql-{_slugify(source_name)}"

    ddl_text = load_ddl_text(ddl_source)
    model = parse_postgres_ddl(ddl_text)
    define_query = generate_define_from_ddl(model, namespace="gra")

    apply_result = apply_layer_a_schema(
        config=config,
        registration_id=reg_id,
        define_query=define_query,
        redefine=False,
    )

    store = LayerCStore(config, ensure_schema=True)
    store.upsert_registered_source(
        RegisteredSourceInput(
            registration_id=reg_id,
            source_name=source_name,
            source_kind="sql",
            source_url=source_url,
            source_description=f"SQL source '{source_name}'",
            source_is_active=True,
            credential_ref_id=f"cred-{reg_id}",
            secret_provider="env",
            secret_ref=f"env://{reg_id.upper().replace('-', '_')}_DSN",
        )
    )
    store.upsert_setting("active_registration_id", reg_id)
    trigger_post_registration_sync(config, reg_id, source_kind="sql")

    return RegistrationPreview(
        registration_id=reg_id,
        source_name=source_name,
        source_kind="sql",
        source_url=source_url,
        layer_a_db=apply_result.layer_a_db,
        tables=tuple(t.name for t in model.tables),
    )


def list_registered_sources(config: AppConfig) -> list[dict]:
    store = LayerCStore(config, ensure_schema=True)
    docs = store.fetch_registered_sources()
    return docs


def set_active_registration(config: AppConfig, registration_id: str) -> str:
    store = LayerCStore(config, ensure_schema=True)
    store.upsert_setting("active_registration_id", registration_id)
    return registration_id


def expected_layer_a_db_for_registration(config: AppConfig, registration_id: str) -> str:
    return layer_a_db_name(config, registration_id)
