from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from typedb.driver import TransactionType

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.database_lifecycle import bootstrap_core_databases
from rpa_plugin_skill.core.typedb_bootstrap import connect_with_retry

BASE_DIR = Path(__file__).resolve().parent.parent
MANIFEST = BASE_DIR / "schema" / "layer_c" / "manifest.json"


@dataclass(frozen=True)
class Migration:
    id: str
    file: str
    marker_label: str
    description: str


def _load_manifest() -> list[Migration]:
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [Migration(**entry) for entry in entries]


def _schema_contains_marker(schema_text: str, marker_label: str) -> bool:
    return marker_label in schema_text


def apply_layer_c_migrations(config: AppConfig) -> list[str]:
    bootstrap_core_databases(config)
    driver = connect_with_retry(config)
    applied: list[str] = []
    try:
        db = driver.databases.get(config.layer_c_db)
        current_schema = db.schema()
        for migration in _load_manifest():
            if _schema_contains_marker(current_schema, migration.marker_label):
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


def main() -> int:
    config = AppConfig.from_env()
    applied = apply_layer_c_migrations(config)
    if applied:
        print(f"[layer_c_migrate] Applied migrations: {', '.join(applied)}")
    else:
        print("[layer_c_migrate] No pending migrations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
