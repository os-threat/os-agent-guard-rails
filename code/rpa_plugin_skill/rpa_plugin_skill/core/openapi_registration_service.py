from __future__ import annotations

import re
from dataclasses import dataclass

from .config import AppConfig
from .database_lifecycle import layer_a_db_name
from .layer_c_store import LayerCStore, RegisteredSourceInput
from .openapi_ingest import load_openapi_text, parse_openapi_document
from .openapi_to_typeql import apply_openapi_layer_a_schema, build_extract_bundles
from .sync_trigger_service import trigger_post_registration_sync


@dataclass(frozen=True)
class ApiRegistrationPreview:
    registration_id: str
    source_name: str
    source_kind: str
    source_url: str
    layer_a_db: str
    component_entities: tuple[str, ...]
    path_templates: tuple[str, ...]
    extract_operations: tuple[str, ...]


def _slugify(value: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "source"


def register_api_source(
    config: AppConfig,
    source_name: str,
    spec_source: str,
    source_url: str,
    registration_id: str | None = None,
) -> ApiRegistrationPreview:
    reg_id = registration_id or f"api-{_slugify(source_name)}"

    spec_text = load_openapi_text(spec_source)
    doc = parse_openapi_document(spec_text)
    layer_a_db = apply_openapi_layer_a_schema(config, reg_id, doc)
    bundles = build_extract_bundles(doc)

    components = doc.get("components", {}) if isinstance(doc.get("components"), dict) else {}
    schemas = components.get("schemas", {}) if isinstance(components.get("schemas"), dict) else {}
    component_entities = tuple(sorted(str(name) for name in schemas.keys()))

    paths = doc.get("paths", {}) if isinstance(doc.get("paths"), dict) else {}
    path_templates = tuple(sorted(str(path) for path in paths.keys()))

    store = LayerCStore(config, ensure_schema=True)
    store.upsert_registered_source(
        RegisteredSourceInput(
            registration_id=reg_id,
            source_name=source_name,
            source_kind="api",
            source_url=source_url,
            source_description=f"OpenAPI source '{source_name}'",
            source_is_active=True,
            credential_ref_id=f"cred-{reg_id}",
            secret_provider="env",
            secret_ref=f"env://{reg_id.upper().replace('-', '_')}_TOKEN",
        )
    )
    store.upsert_setting("active_registration_id", reg_id)
    trigger_post_registration_sync(config, reg_id, source_kind="api")

    return ApiRegistrationPreview(
        registration_id=reg_id,
        source_name=source_name,
        source_kind="api",
        source_url=source_url,
        layer_a_db=layer_a_db,
        component_entities=component_entities,
        path_templates=path_templates,
        extract_operations=tuple(sorted(bundle.operation_id for bundle in bundles)),
    )


def expected_layer_a_db_for_registration(config: AppConfig, registration_id: str) -> str:
    return layer_a_db_name(config, registration_id)
