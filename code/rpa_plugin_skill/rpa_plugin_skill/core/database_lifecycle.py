from __future__ import annotations

import hashlib
import re

from .config import AppConfig
from .typedb_bootstrap import connect_with_retry

SAFE_ID_PATTERN = re.compile(r"[^a-zA-Z0-9_\-]")


def _sanitize_registration_id(registration_id: str) -> str:
    token = SAFE_ID_PATTERN.sub("_", registration_id.strip().lower())
    token = re.sub(r"_+", "_", token)
    return token.strip("_") or "source"


def layer_a_db_name(config: AppConfig, registration_id: str) -> str:
    sanitized = _sanitize_registration_id(registration_id)
    digest = hashlib.sha1(registration_id.encode("utf-8")).hexdigest()[:8]
    base = f"{config.layer_a_prefix}{sanitized}_{digest}"
    if len(base) <= config.max_database_name_length:
        return base

    trim_len = config.max_database_name_length - len(config.layer_a_prefix) - len(digest) - 1
    trimmed = sanitized[: max(trim_len, 1)]
    return f"{config.layer_a_prefix}{trimmed}_{digest}"


def bootstrap_core_databases(config: AppConfig) -> list[str]:
    created: list[str] = []
    driver = connect_with_retry(config)
    try:
        for name in (config.layer_c_db, config.layer_b_db):
            if not driver.databases.contains(name):
                driver.databases.create(name)
                created.append(name)
    finally:
        driver.close()
    return created


def ensure_layer_a_database(config: AppConfig, registration_id: str) -> str:
    name = layer_a_db_name(config, registration_id)
    driver = connect_with_retry(config)
    try:
        if not driver.databases.contains(name):
            driver.databases.create(name)
    finally:
        driver.close()
    return name


def list_databases(config: AppConfig) -> list[str]:
    driver = connect_with_retry(config)
    try:
        return sorted(db.name for db in driver.databases.all())
    finally:
        driver.close()


def archive_layer_a_database(config: AppConfig, registration_id: str) -> str:
    """Archive lifecycle in v1: drop the mapped Layer A database.

    TypeDB does not provide a first-class rename/archive API for databases in this workflow,
    so archive is implemented as delete-by-name of the deterministic Layer A mapping.
    """
    name = layer_a_db_name(config, registration_id)
    driver = connect_with_retry(config)
    try:
        if driver.databases.contains(name):
            db = driver.databases.get(name)
            db.delete()
    finally:
        driver.close()
    return name
