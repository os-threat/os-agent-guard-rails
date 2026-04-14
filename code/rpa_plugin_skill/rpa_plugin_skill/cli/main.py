from __future__ import annotations

import argparse
import json

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.database_lifecycle import (
    archive_layer_a_database,
    bootstrap_core_databases,
    ensure_layer_a_database,
    list_databases,
)
from rpa_plugin_skill.core.guard_mcp_registry import GuardMcpRegistry
from rpa_plugin_skill.core.health import probe_typedb
from rpa_plugin_skill.core.nl_rule_codegen import RuleValidationError
from rpa_plugin_skill.core.openapi_registration_service import register_api_source
from rpa_plugin_skill.core.rule_composer import compose_rule_preview
from rpa_plugin_skill.core.rule_service import (
    archive_rule_for_source,
    delete_rule_for_source,
    list_rules_for_source,
    upsert_rule_for_source,
    upsert_rule_from_nl_for_source,
)
from rpa_plugin_skill.core.sql_registration_service import (
    list_registered_sources,
    register_sql_source,
    set_active_registration,
)
from rpa_plugin_skill.core.sql_sync_worker import SqlSyncPlan, sync_sql_rows_to_layer_a


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
    parser.add_argument("--rule-source", metavar="REG_ID", help="Rule source registration id.")
    parser.add_argument("--rule-id", metavar="RULE_ID", help="Rule identifier.")
    parser.add_argument("--rule-name", metavar="RULE_NAME", help="Rule display name.")
    parser.add_argument("--rule-nl", metavar="TEXT", help="Natural-language rule text.")
    parser.add_argument("--rule-horn", metavar="TEXT", help="Horn-clause form for the rule.")
    parser.add_argument(
        "--rule-typeql",
        metavar="QUERY",
        help="TypeQL schema/function query linked to the rule.",
    )
    parser.add_argument("--rule-ast-ref", metavar="REF", help="Rule AST reference.")
    parser.add_argument(
        "--rule-status",
        metavar="STATUS",
        default="draft",
        help="Rule status: draft|active|archived (default: draft).",
    )
    parser.add_argument(
        "--rule-list",
        action="store_true",
        help="List rules for --rule-source.",
    )
    parser.add_argument(
        "--rule-upsert",
        action="store_true",
        help="Upsert rule metadata and associated Layer A logic.",
    )
    parser.add_argument(
        "--rule-codegen-from-nl",
        action="store_true",
        help="Generate Horn AST/TypeQL fun from --rule-nl before upsert.",
    )
    parser.add_argument(
        "--rule-archive",
        action="store_true",
        help="Archive a rule in Layer C (tombstone semantics).",
    )
    parser.add_argument(
        "--rule-delete",
        action="store_true",
        help="Hard-delete rule metadata from Layer C.",
    )
    parser.add_argument(
        "--rule-undefine-query",
        metavar="QUERY",
        help="Optional TypeQL undefine query for --rule-delete.",
    )
    parser.add_argument(
        "--rule-compose-preview",
        action="store_true",
        help="Render rule composer payload (NL left; Logic/TypeQL tabs right).",
    )
    parser.add_argument(
        "--guard-mcp-source",
        metavar="REG_ID",
        help="Registration id for Guard MCP registry refresh/list.",
    )
    parser.add_argument(
        "--guard-mcp-refresh",
        action="store_true",
        help="Refresh in-process Guard MCP tool registry from Layer C (no process restart).",
    )
    parser.add_argument(
        "--guard-mcp-list-tools",
        action="store_true",
        help="List Guard MCP tool names (implies refresh for this process).",
    )
    parser.add_argument(
        "--sync-sql-source",
        metavar="REG_ID",
        help="Registration id for SQL->Layer A sync worker.",
    )
    parser.add_argument(
        "--sync-sql-dsn",
        metavar="DSN",
        help="Postgres DSN for SQL sync worker query execution.",
    )
    parser.add_argument(
        "--sync-sql-query",
        metavar="QUERY",
        help="SQL query text for sync worker extraction.",
    )
    parser.add_argument(
        "--sync-sql-table",
        metavar="TABLE",
        help="Logical SQL table name for Layer A entity/attribute mapping.",
    )
    parser.add_argument(
        "--sync-watermark-column",
        metavar="COLUMN",
        help="Optional SQL watermark column for incremental syncs.",
    )
    parser.add_argument(
        "--sync-watermark-gt",
        metavar="VALUE",
        help="Optional watermark lower bound (exclusive).",
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

    if args.rule_list:
        if not args.rule_source:
            raise SystemExit("--rule-list requires --rule-source")
        docs = list_rules_for_source(config, args.rule_source)
        print(f"[rpa_plugin_skill] RULES source={args.rule_source} docs={docs}")

    if args.rule_upsert:
        try:
            if args.rule_codegen_from_nl:
                required_codegen = [
                    args.rule_source,
                    args.rule_id,
                    args.rule_name,
                    args.rule_nl,
                ]
                if not all(required_codegen):
                    raise SystemExit(
                        "--rule-upsert --rule-codegen-from-nl requires "
                        "--rule-source --rule-id --rule-name --rule-nl"
                    )
                preview = upsert_rule_from_nl_for_source(
                    config=config,
                    registration_id=args.rule_source,
                    rule_id=args.rule_id,
                    rule_name=args.rule_name,
                    nl_text=args.rule_nl,
                    status=args.rule_status,
                )
            else:
                required_manual = [
                    args.rule_source,
                    args.rule_id,
                    args.rule_name,
                    args.rule_nl,
                    args.rule_horn,
                    args.rule_typeql,
                    args.rule_ast_ref,
                ]
                if not all(required_manual):
                    raise SystemExit(
                        "--rule-upsert requires --rule-source --rule-id --rule-name --rule-nl "
                        "--rule-horn --rule-typeql --rule-ast-ref "
                        "(or use --rule-codegen-from-nl)"
                    )
                preview = upsert_rule_for_source(
                    config=config,
                    registration_id=args.rule_source,
                    rule_id=args.rule_id,
                    rule_name=args.rule_name,
                    nl_text=args.rule_nl,
                    horn_text=args.rule_horn,
                    typeql_fun=args.rule_typeql,
                    ast_ref=args.rule_ast_ref,
                    status=args.rule_status,
                )
        except RuleValidationError as exc:
            raise SystemExit(f"Invalid rule: {exc}") from exc

        print(
            "[rpa_plugin_skill] RULE_UPSERT "
            f"source={preview.registration_id} rule_id={preview.rule_id} "
            f"status={preview.rule_status} layer_a_db={preview.layer_a_db}"
        )

    if args.rule_archive:
        if not (args.rule_source and args.rule_id):
            raise SystemExit("--rule-archive requires --rule-source and --rule-id")
        archive_rule_for_source(config, args.rule_source, args.rule_id)
        print(
            f"[rpa_plugin_skill] RULE_ARCHIVE source={args.rule_source} rule_id={args.rule_id}"
        )

    if args.rule_delete:
        if not (args.rule_source and args.rule_id):
            raise SystemExit("--rule-delete requires --rule-source and --rule-id")
        delete_rule_for_source(
            config=config,
            registration_id=args.rule_source,
            rule_id=args.rule_id,
            undefine_query=args.rule_undefine_query,
        )
        print(
            f"[rpa_plugin_skill] RULE_DELETE source={args.rule_source} rule_id={args.rule_id}"
        )

    if args.rule_compose_preview:
        if not (args.rule_id and args.rule_name and args.rule_nl):
            raise SystemExit(
                "--rule-compose-preview requires --rule-id --rule-name --rule-nl"
            )
        try:
            preview = compose_rule_preview(
                rule_id=args.rule_id,
                rule_name=args.rule_name,
                nl_text=args.rule_nl,
            )
        except RuleValidationError as exc:
            raise SystemExit(f"Invalid rule: {exc}") from exc
        payload = {
            "nl_left": preview.nl_text,
            "logic_tab": {
                "horn_clause": preview.logic_tab.horn_clause,
                "diagram_mermaid": preview.logic_tab.diagram_mermaid,
            },
            "typeql_tab": {
                "mode": preview.typeql_tab.mode,
                "function_label": preview.typeql_tab.function_label,
                "function_define_query": preview.typeql_tab.function_define_query,
            },
            "ast_ref": preview.ast_ref,
        }
        rendered = json.dumps(payload, ensure_ascii=True)
        print(f"[rpa_plugin_skill] RULE_COMPOSER {rendered}")

    if args.guard_mcp_refresh or args.guard_mcp_list_tools:
        if not args.guard_mcp_source:
            raise SystemExit(
                "--guard-mcp-source is required for --guard-mcp-refresh / --guard-mcp-list-tools"
            )
        registry = GuardMcpRegistry(config)
        generation = registry.refresh(args.guard_mcp_source)
        names = registry.list_tool_names()
        print(
            "[rpa_plugin_skill] GUARD_MCP "
            f"source={args.guard_mcp_source} generation={generation} "
            f"tools={','.join(names)}"
        )

    if (
        args.sync_sql_source
        or args.sync_sql_dsn
        or args.sync_sql_query
        or args.sync_sql_table
    ):
        required_sync = [
            args.sync_sql_source,
            args.sync_sql_dsn,
            args.sync_sql_query,
            args.sync_sql_table,
        ]
        if not all(required_sync):
            raise SystemExit(
                "--sync-sql-source --sync-sql-dsn --sync-sql-query --sync-sql-table "
                "must be provided together"
            )
        plan = SqlSyncPlan(
            registration_id=args.sync_sql_source,
            sql_dsn=args.sync_sql_dsn,
            sql_query=args.sync_sql_query,
            source_table=args.sync_sql_table,
            watermark_column=args.sync_watermark_column,
            watermark_gt=args.sync_watermark_gt,
        )
        result = sync_sql_rows_to_layer_a(config, plan)
        print(
            "[rpa_plugin_skill] SQL_SYNC "
            f"source={result.registration_id} layer_a_db={result.layer_a_db} "
            f"rows_synced={result.rows_synced} watermark_max={result.watermark_max}"
        )

    if args.list_databases:
        dbs = list_databases(config)
        print(f"[rpa_plugin_skill] DATABASES {', '.join(dbs)}")

    print("[rpa_plugin_skill] Skeleton startup complete.")
    return 0
