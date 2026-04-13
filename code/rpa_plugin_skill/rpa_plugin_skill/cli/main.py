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
from rpa_plugin_skill.core.openapi_registration_service import register_api_source
from rpa_plugin_skill.core.sql_registration_service import (
    list_registered_sources,
    register_sql_source,
    set_active_registration,
)


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
    parser.add_argument(
        "--register-sql-name",
        metavar="NAME",
        help="Register a SQL source by name (requires --register-sql-ddl and --register-sql-url).",
    )
    parser.add_argument(
        "--register-sql-ddl",
        metavar="DDL",
        help="DDL input for SQL registration (inline text, local path, or URL).",
    )
    parser.add_argument(
        "--register-sql-url",
        metavar="URL",
        help="SQL source URL/DSN label for registration metadata.",
    )
    parser.add_argument(
        "--activate-source",
        metavar="REG_ID",
        help="Switch active registration context in Layer C settings.",
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="List registered sources from Layer C.",
    )
    parser.add_argument(
        "--register-api-name",
        metavar="NAME",
        help=(
            "Register an OpenAPI source by name "
            "(requires --register-api-spec and --register-api-url)."
        ),
    )
    parser.add_argument(
        "--register-api-spec",
        metavar="SPEC",
        help="OpenAPI source (inline text, local path, or URL).",
    )
    parser.add_argument(
        "--register-api-url",
        metavar="URL",
        help="API base URL label for registration metadata.",
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

    if args.register_sql_name or args.register_sql_ddl or args.register_sql_url:
        if not (args.register_sql_name and args.register_sql_ddl and args.register_sql_url):
            msg = (
                "--register-sql-name, --register-sql-ddl, and --register-sql-url "
                "must be provided together"
            )
            raise SystemExit(
                msg
            )
        preview = register_sql_source(
            config=config,
            source_name=args.register_sql_name,
            ddl_source=args.register_sql_ddl,
            source_url=args.register_sql_url,
        )
        print(
            "[rpa_plugin_skill] SQL registration completed "
            f"registration_id={preview.registration_id} layer_a_db={preview.layer_a_db} "
            f"tables={','.join(preview.tables)}"
        )

    if args.register_api_name or args.register_api_spec or args.register_api_url:
        if not (args.register_api_name and args.register_api_spec and args.register_api_url):
            msg = (
                "--register-api-name, --register-api-spec, and --register-api-url "
                "must be provided together"
            )
            raise SystemExit(msg)
        preview = register_api_source(
            config=config,
            source_name=args.register_api_name,
            spec_source=args.register_api_spec,
            source_url=args.register_api_url,
        )
        print(
            "[rpa_plugin_skill] API registration completed "
            f"registration_id={preview.registration_id} layer_a_db={preview.layer_a_db} "
            f"components={','.join(preview.component_entities)} "
            f"paths={','.join(preview.path_templates)} "
            f"extract_ops={','.join(preview.extract_operations)}"
        )

    if args.activate_source:
        active = set_active_registration(config, args.activate_source)
        print(f"[rpa_plugin_skill] Active registration set to {active}")

    if args.list_sources:
        docs = list_registered_sources(config)
        print(f"[rpa_plugin_skill] SOURCES {docs}")

    if args.list_databases:
        dbs = list_databases(config)
        print(f"[rpa_plugin_skill] DATABASES {', '.join(dbs)}")

    print("[rpa_plugin_skill] Skeleton startup complete.")
    return 0
