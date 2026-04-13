from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .config import AppConfig
from .sql_to_typeql import apply_layer_a_schema


@dataclass(frozen=True)
class ExtractBundle:
    operation_id: str
    method: str
    path: str
    source_pointer: str
    response_jsonpath: str
    parameter_bindings: dict[str, str]


def generate_define_from_openapi(doc: dict[str, Any], namespace: str = "gra") -> str:
    lines: list[str] = ["define"]

    components = doc.get("components", {}) if isinstance(doc.get("components"), dict) else {}
    schemas = components.get("schemas", {}) if isinstance(components.get("schemas"), dict) else {}

    for schema_name, schema in schemas.items():
        props = schema.get("properties", {}) if isinstance(schema, dict) else {}
        for prop_name, prop in props.items():
            attr = _attr_label(namespace, schema_name, prop_name)
            value_type = _openapi_type_to_typeql(prop)
            lines.append(f"  attribute {attr}, value {value_type};")

    if schemas:
        lines.append("")

    for schema_name, schema in schemas.items():
        props = schema.get("properties", {}) if isinstance(schema, dict) else {}
        required = set(schema.get("required", []) if isinstance(schema, dict) else [])
        entity = _entity_label(namespace, schema_name)
        owns_parts: list[str] = []

        key_candidate = _key_candidate(props)
        for prop_name in props.keys():
            attr = _attr_label(namespace, schema_name, prop_name)
            if key_candidate and prop_name == key_candidate:
                owns_parts.append(f"owns {attr} @key")
            else:
                if prop_name in required:
                    owns_parts.append(f"owns {attr}")
                else:
                    owns_parts.append(f"owns {attr} @card(0..1)")

        if owns_parts:
            lines.append(f"  entity {entity},")
            for idx, part in enumerate(owns_parts):
                suffix = "," if idx < len(owns_parts) - 1 else ";"
                lines.append(f"    {part}{suffix}")
        else:
            lines.append(f"  entity {entity};")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def build_extract_bundles(doc: dict[str, Any]) -> list[ExtractBundle]:
    bundles: list[ExtractBundle] = []
    paths = doc.get("paths", {}) if isinstance(doc.get("paths"), dict) else {}

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(operation, dict):
                continue

            operation_id = operation.get("operationId") or _fallback_operation_id(
                method, path
            )
            raw_params = operation.get("parameters")
            params = raw_params if isinstance(raw_params, list) else []
            bindings: dict[str, str] = {}
            for p in params:
                if not isinstance(p, dict):
                    continue
                pname = p.get("name")
                pin = p.get("in")
                if isinstance(pname, str) and isinstance(pin, str):
                    bindings[pname] = f"$.params.{pin}.{pname}"

            bundles.append(
                ExtractBundle(
                    operation_id=operation_id,
                    method=method.upper(),
                    path=path,
                    source_pointer=f"paths.{path}.{method}",
                    response_jsonpath="$.responses.200.body",
                    parameter_bindings=bindings,
                )
            )

    return bundles


def apply_openapi_layer_a_schema(
    config: AppConfig,
    registration_id: str,
    openapi_doc: dict[str, Any],
) -> str:
    query = generate_define_from_openapi(openapi_doc, namespace="gra")
    result = apply_layer_a_schema(
        config=config,
        registration_id=registration_id,
        define_query=query,
        redefine=False,
    )
    return result.layer_a_db


def _entity_label(namespace: str, name: str) -> str:
    return f"{_safe(namespace)}_{_safe(name)}"


def _attr_label(namespace: str, schema_name: str, prop_name: str) -> str:
    return f"{_safe(namespace)}_{_safe(schema_name)}_{_safe(prop_name)}"


def _safe(value: str) -> str:
    label = re.sub(r"[^a-zA-Z0-9_]", "_", value.strip().lower())
    label = re.sub(r"_+", "_", label).strip("_")
    if not label:
        label = "x"
    if label[0].isdigit():
        label = f"x_{label}"
    return label


def _openapi_type_to_typeql(prop: dict[str, Any]) -> str:
    ptype = str(prop.get("type", "string")).lower()
    fmt = str(prop.get("format", "")).lower()

    if ptype == "integer":
        return "integer"
    if ptype == "number":
        if fmt in {"double", "float"}:
            return "double"
        return "decimal"
    if ptype == "boolean":
        return "boolean"
    if ptype == "string" and fmt in {"date-time", "datetime"}:
        return "datetime"
    if ptype == "string" and fmt == "date":
        return "date"
    return "string"


def _key_candidate(properties: dict[str, Any]) -> str | None:
    for candidate in ("id", "uuid", "external_id"):
        if candidate in properties:
            return candidate
    return None


def _fallback_operation_id(method: str, path: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", path.strip("/"))
    clean = re.sub(r"_+", "_", clean).strip("_") or "root"
    return f"{method.lower()}_{clean}"
