from __future__ import annotations

import argparse

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.database_lifecycle import (
    archive_layer_a_database,
    bootstrap_core_databases,
    ensure_layer_a_database,
    list_databases,
)
from rpa_plugin_skill.core.health import probe_typedb


def main() -> int:
    parser = argparse.ArgumentParser(description="RPA plugin/skill skeleton")
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Create missing Layer C/B databases on the configured TypeDB instance.",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Probe TypeDB connectivity for UI/workers and print a machine-readable status line.",
    )
    parser.add_argument(
        "--register-source",
        metavar="REG_ID",
        help="Create/get deterministic Layer A database name for a source registration id.",
    )
    parser.add_argument(
        "--archive-source",
        metavar="REG_ID",
        help="Archive (delete in v1) the deterministic Layer A database for a registration id.",
    )
    parser.add_argument(
        "--list-databases",
        action="store_true",
        help="List databases visible on the configured TypeDB instance.",
    )
    args = parser.parse_args()

    config = AppConfig.from_env()
    print(f"[rpa_plugin_skill] TypeDB address: {config.typedb_address}")
    print(
        "[rpa_plugin_skill] Database targets: "
        f"C={config.layer_c_db}, B={config.layer_b_db}, A_test={config.layer_a_test_db}"
    )

    if args.health:
        result = probe_typedb(config)
        if result.ok:
            print(
                f"[rpa_plugin_skill] HEALTH_OK address={result.address} "
                f"database_count={result.database_count}"
            )
        else:
            print(
                f"[rpa_plugin_skill] HEALTH_FAIL address={result.address} "
                f"error={result.error}"
            )
            return 1

    if args.bootstrap:
        created = bootstrap_core_databases(config)
        if created:
            print(f"[rpa_plugin_skill] Created core databases: {', '.join(created)}")
        else:
            print("[rpa_plugin_skill] Core databases already exist.")

    if args.register_source:
        name = ensure_layer_a_database(config, args.register_source)
        print(
            "[rpa_plugin_skill] Layer A mapping created_or_exists "
            f"source={args.register_source} db={name}"
        )

    if args.archive_source:
        name = archive_layer_a_database(config, args.archive_source)
        print(
            "[rpa_plugin_skill] Layer A mapping archived "
            f"source={args.archive_source} db={name}"
        )

    if args.list_databases:
        dbs = list_databases(config)
        print(f"[rpa_plugin_skill] DATABASES {', '.join(dbs)}")

    print("[rpa_plugin_skill] Skeleton startup complete.")
    return 0
