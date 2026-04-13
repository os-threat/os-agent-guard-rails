from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from typedb.driver import TransactionType

from .config import AppConfig
from .database_lifecycle import bootstrap_core_databases
from .typedb_bootstrap import connect_with_retry

BASE_DIR = Path(__file__).resolve().parents[2]
MANIFEST = BASE_DIR / "schema" / "layer_c" / "manifest.json"


@dataclass(frozen=True)
class Migration:
    id: str
    file: str
    marker_label: str
    description: str


def load_manifest() -> list[Migration]:
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [Migration(**entry) for entry in entries]


def schema_contains_marker(schema_text: str, marker_label: str) -> bool:
    return marker_label in schema_text


def apply_layer_c_migrations(config: AppConfig) -> list[str]:
    bootstrap_core_databases(config)
    driver = connect_with_retry(config)
    applied: list[str] = []
    try:
        db = driver.databases.get(config.layer_c_db)
        current_schema = db.schema()
        for migration in load_manifest():
            if schema_contains_marker(current_schema, migration.marker_label):
                continue

            path = MANIFEST.parent / migration.file
            query = path.read_text(encoding="utf-8").strip()
            with driver.transaction(config.layer_c_db, TransactionType.SCHEMA) as tx:
                tx.query(query).resolve()
                tx.commit()
            applied.append(migration.id)
            current_schema = db.schema()
    finally:
        driver.close()
    return applied
