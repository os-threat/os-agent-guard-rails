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
from rpa_plugin_skill.core.mcp_server import PluginMcpServer
from rpa_plugin_skill.core.nl_rule_codegen import RuleValidationError
from rpa_plugin_skill.core.openapi_registration_service import register_api_source
from rpa_plugin_skill.core.openapi_to_typeql import ExtractBundle
from rpa_plugin_skill.core.rest_sync_worker import RestSyncPlan
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
from rpa_plugin_skill.core.sql_sync_worker import SqlSyncPlan
from rpa_plugin_skill.core.sync_trigger_service import (
    get_sync_status,
    trigger_manual_rest_sync,
    trigger_manual_sql_sync,
    trigger_post_task_finalize_sync,
)
from rpa_plugin_skill.core.task_composer import compose_task_preview


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
        "--task-source",
        metavar="REG_ID",
        help="Task source registration id for task composer preview.",
    )
    parser.add_argument(
        "--task-description",
        metavar="TEXT",
        help="Task description text for composer preview.",
    )
    parser.add_argument(
        "--task-compose-preview",
        action="store_true",
        help="Render task composer payload (description left; flow chart right).",
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
    parser.add_argument(
        "--sync-rest-source",
        metavar="REG_ID",
        help="Registration id for REST->Layer A sync worker.",
    )
    parser.add_argument(
        "--sync-rest-base-url",
        metavar="URL",
        help="Base REST URL for extract bundle execution.",
    )
    parser.add_argument(
        "--sync-rest-path",
        metavar="PATH",
        help="REST path for extract bundle call (example: /clients).",
    )
    parser.add_argument(
        "--sync-rest-method",
        metavar="METHOD",
        default="GET",
        help="HTTP method for extract bundle call (default: GET).",
    )
    parser.add_argument(
        "--sync-rest-target-entity",
        metavar="ENTITY",
        help="Layer A entity label for mapped REST rows (example: gra_client).",
    )
    parser.add_argument(
        "--sync-rest-records-key",
        metavar="KEY",
        help="Optional response key containing row array (example: data).",
    )
    parser.add_argument(
        "--sync-rest-pagination",
        metavar="MODE",
        default="none",
        help="Pagination mode: none|next_link (default: none).",
    )
    parser.add_argument(
        "--sync-rest-max-pages",
        metavar="N",
        type=int,
        default=1,
        help="Maximum pages to fetch for REST sync (default: 1).",
    )
    parser.add_argument(
        "--sync-rest-rate-limit-ms",
        metavar="MS",
        type=int,
        default=0,
        help="Sleep between paged requests in milliseconds (default: 0).",
    )
    parser.add_argument(
        "--sync-status-source",
        metavar="REG_ID",
        help="Show last sync status for registration id (time/error/rows/trigger).",
    )
    parser.add_argument(
        "--sync-task-finalize-source",
        metavar="REG_ID",
        help="Registration id for post-task-finalize sync trigger hook.",
    )
    parser.add_argument(
        "--sync-task-finalize-task-id",
        metavar="TASK_ID",
        help="Task id used for post-task-finalize sync trigger hook.",
    )
    parser.add_argument(
        "--mcp-list-namespaces",
        action="store_true",
        help="List MCP namespaces exposed by the long-lived plugin server scaffold.",
    )
    parser.add_argument(
        "--mcp-list-tools-namespace",
        metavar="NAMESPACE",
        help="List tools for a given MCP namespace (guard|promise).",
    )
    parser.add_argument(
        "--mcp-guard-source",
        metavar="REG_ID",
        help="Optional guard registration id used to refresh guard namespace tools.",
    )
    parser.add_argument(
        "--mcp-guard-invoke-tool",
        metavar="TOOL",
        help="Invoke a guard MCP tool (example: guard.gr_guard_fp_r01).",
    )
    parser.add_argument(
        "--mcp-guard-subject-key",
        metavar="KEY",
        help="Subject key for guard tool invocation.",
    )
    parser.add_argument(
        "--mcp-guard-introspect-tool",
        metavar="TOOL",
        help="Show data-trace introspection for a guard tool.",
    )
    parser.add_argument(
        "--mcp-promise-invoke-tool",
        metavar="TOOL",
        help="Invoke promise MCP tool (declare|chain|assess|query).",
    )
    parser.add_argument(
        "--mcp-promise-payload-json",
        metavar="JSON",
        help="JSON payload string used with --mcp-promise-invoke-tool.",
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

    if args.task_compose_preview:
        if not (args.task_source and args.task_description):
            raise SystemExit(
                "--task-compose-preview requires --task-source and --task-description"
            )
        preview = compose_task_preview(
            config=config,
            registration_id=args.task_source,
            description=args.task_description,
        )
        payload = {
            "description_left": preview.description,
            "flow_chart_right": {
                "diagram_mermaid": preview.diagram_mermaid,
                "steps": [
                    {"id": step.step_id, "title": step.title, "detail": step.detail}
                    for step in preview.flow_steps
                ],
            },
            "schema_highlights": [
                {"label": item.label, "kind": item.kind}
                for item in preview.highlighted_objects
            ],
            "process_highlights": preview.highlighted_process_terms,
            "layer_a_db": preview.layer_a_db,
            "registration_id": preview.registration_id,
        }
        rendered = json.dumps(payload, ensure_ascii=True)
        print(f"[rpa_plugin_skill] TASK_COMPOSER {rendered}")

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
        status = trigger_manual_sql_sync(config, plan)
        print(
            "[rpa_plugin_skill] SQL_SYNC "
            f"source={status.registration_id} rows_synced={status.last_sync_rows} "
            f"last_time={status.last_sync_time} error={status.last_sync_error}"
        )

    if (
        args.sync_rest_source
        or args.sync_rest_base_url
        or args.sync_rest_path
        or args.sync_rest_target_entity
    ):
        required_rest = [
            args.sync_rest_source,
            args.sync_rest_base_url,
            args.sync_rest_path,
            args.sync_rest_target_entity,
        ]
        if not all(required_rest):
            raise SystemExit(
                "--sync-rest-source --sync-rest-base-url --sync-rest-path "
                "--sync-rest-target-entity must be provided together"
            )
        bundle = ExtractBundle(
            operation_id=f"sync_{args.sync_rest_method.lower()}_{args.sync_rest_path.strip('/')}",
            method=args.sync_rest_method.upper(),
            path=args.sync_rest_path,
            source_pointer=f"paths.{args.sync_rest_path}.{args.sync_rest_method.lower()}",
            response_jsonpath="$.responses.200.body",
            parameter_bindings={},
        )
        plan = RestSyncPlan(
            registration_id=args.sync_rest_source,
            base_url=args.sync_rest_base_url,
            bundle=bundle,
            target_entity=args.sync_rest_target_entity,
            response_records_key=args.sync_rest_records_key,
            pagination_mode=args.sync_rest_pagination,
            max_pages=args.sync_rest_max_pages,
            rate_limit_sleep_ms=args.sync_rest_rate_limit_ms,
        )
        status = trigger_manual_rest_sync(config, plan)
        print(
            "[rpa_plugin_skill] REST_SYNC "
            f"source={status.registration_id} rows_synced={status.last_sync_rows} "
            f"last_time={status.last_sync_time} error={status.last_sync_error}"
        )

    if args.sync_task_finalize_source or args.sync_task_finalize_task_id:
        if not (args.sync_task_finalize_source and args.sync_task_finalize_task_id):
            raise SystemExit(
                "--sync-task-finalize-source and --sync-task-finalize-task-id "
                "must be provided together"
            )
        status = trigger_post_task_finalize_sync(
            config=config,
            registration_id=args.sync_task_finalize_source,
            task_id=args.sync_task_finalize_task_id,
        )
        print(
            "[rpa_plugin_skill] SYNC_TASK_FINALIZE "
            f"source={status.registration_id} trigger={status.last_sync_trigger} "
            f"last_time={status.last_sync_time}"
        )

    if args.sync_status_source:
        status = get_sync_status(config, args.sync_status_source)
        print(
            "[rpa_plugin_skill] SYNC_STATUS "
            f"source={status.registration_id} last_time={status.last_sync_time} "
            f"last_error={status.last_sync_error} last_rows={status.last_sync_rows} "
            f"last_trigger={status.last_sync_trigger}"
        )

    if (
        args.mcp_list_namespaces
        or args.mcp_list_tools_namespace
        or args.mcp_guard_invoke_tool
        or args.mcp_guard_introspect_tool
        or args.mcp_promise_invoke_tool
    ):
        server = PluginMcpServer(config)
        if args.mcp_guard_source:
            generation = server.set_guard_source(args.mcp_guard_source)
            print(
                "[rpa_plugin_skill] MCP_GUARD_REFRESH "
                f"source={args.mcp_guard_source} generation={generation}"
            )
        if args.mcp_list_namespaces:
            namespaces = server.list_namespaces()
            print(f"[rpa_plugin_skill] MCP_NAMESPACES {','.join(namespaces)}")
        if args.mcp_list_tools_namespace:
            tools = server.list_tools(args.mcp_list_tools_namespace)
            rendered = ",".join(tool.name for tool in tools)
            print(
                "[rpa_plugin_skill] MCP_NAMESPACE_TOOLS "
                f"namespace={args.mcp_list_tools_namespace} tools={rendered}"
            )
        if args.mcp_guard_invoke_tool:
            if not (args.mcp_guard_source and args.mcp_guard_subject_key):
                raise SystemExit(
                    "--mcp-guard-invoke-tool requires --mcp-guard-source and "
                    "--mcp-guard-subject-key"
                )
            result = server.invoke_guard_tool(
                args.mcp_guard_invoke_tool,
                args.mcp_guard_subject_key,
            )
            print(
                "[rpa_plugin_skill] MCP_GUARD_INVOKE "
                f"tool={result.tool_name} decision={result.decision} "
                f"trace={json.dumps(result.data_trace, ensure_ascii=True)}"
            )
        if args.mcp_guard_introspect_tool:
            if not args.mcp_guard_source:
                raise SystemExit(
                    "--mcp-guard-introspect-tool requires --mcp-guard-source"
                )
            trace = server.introspect_guard_tool(args.mcp_guard_introspect_tool)
            print(
                "[rpa_plugin_skill] MCP_GUARD_INTROSPECT "
                f"tool={args.mcp_guard_introspect_tool} "
                f"trace={json.dumps(trace, ensure_ascii=True)}"
            )
        if args.mcp_promise_invoke_tool:
            if not args.mcp_promise_payload_json:
                raise SystemExit(
                    "--mcp-promise-invoke-tool requires --mcp-promise-payload-json"
                )
            try:
                payload = json.loads(args.mcp_promise_payload_json)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON for --mcp-promise-payload-json: {exc}") from exc
            if not isinstance(payload, dict):
                raise SystemExit("--mcp-promise-payload-json must decode to a JSON object")
            result = server.invoke_promise_tool(args.mcp_promise_invoke_tool, payload)
            print(
                "[rpa_plugin_skill] MCP_PROMISE_INVOKE "
                f"tool={result.tool_name} payload={json.dumps(result.payload, ensure_ascii=True)}"
            )

    if args.list_databases:
        dbs = list_databases(config)
        print(f"[rpa_plugin_skill] DATABASES {', '.join(dbs)}")

    print("[rpa_plugin_skill] Skeleton startup complete.")
    return 0
