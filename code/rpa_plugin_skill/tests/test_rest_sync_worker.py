from __future__ import annotations

import json
import threading
import unittest
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from typedb.driver import TransactionType

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.database_lifecycle import layer_a_db_name
from rpa_plugin_skill.core.openapi_to_typeql import ExtractBundle
from rpa_plugin_skill.core.rest_sync_worker import RestSyncPlan, sync_rest_bundle_to_layer_a
from rpa_plugin_skill.core.typedb_bootstrap import connect_with_retry


class _PagedHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path.endswith("page=1"):
            payload = {
                "data": [{"id": 1, "name": "Alice"}],
                "next": f"http://127.0.0.1:{self.server.server_port}/clients?page=2",
            }
        elif self.path.endswith("page=2"):
            payload = {"data": [{"id": 2, "name": "Bob"}], "next": None}
        else:
            payload = {"data": [{"id": 1, "name": "Alice"}], "next": None}

        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


class RestSyncWorkerIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        base = AppConfig.from_env()
        self.cfg = replace(base, typedb_connect_retries=1, typedb_connect_retry_delay_sec=0.1)
        self.registration_id = "api-rest-sync-alpha"
        self.layer_a_db = layer_a_db_name(self.cfg, self.registration_id)
        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            self.skipTest("TypeDB not available for REST sync integration test")

        try:
            if not driver.databases.contains(self.layer_a_db):
                driver.databases.create(self.layer_a_db)
            with driver.transaction(self.layer_a_db, TransactionType.SCHEMA) as tx:
                tx.query(
                    """define
  attribute gra_client_id, value integer;
  attribute gra_client_name, value string;
  entity gra_client,
    owns gra_client_id @key,
    owns gra_client_name;"""
                ).resolve()
                tx.commit()
        finally:
            driver.close()

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _PagedHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            return
        try:
            if driver.databases.contains(self.layer_a_db):
                driver.databases.get(self.layer_a_db).delete()
        finally:
            driver.close()

    def test_rest_sync_paginates_and_inserts_into_layer_a(self) -> None:
        bundle = ExtractBundle(
            operation_id="listClients",
            method="GET",
            path="/clients",
            source_pointer="paths./clients.get",
            response_jsonpath="$.responses.200.body",
            parameter_bindings={},
        )
        plan = RestSyncPlan(
            registration_id=self.registration_id,
            base_url=self.base_url,
            bundle=bundle,
            target_entity="gra_client",
            response_records_key="data",
            pagination_mode="next_link",
            max_pages=5,
            query_params={"page": "1"},
        )
        result = sync_rest_bundle_to_layer_a(self.cfg, plan)
        self.assertEqual(result.pages_fetched, 2)
        self.assertEqual(result.rows_synced, 2)

        driver = connect_with_retry(self.cfg)
        try:
            with driver.transaction(self.layer_a_db, TransactionType.READ) as tx:
                answer = tx.query(
                    """match
  $c isa gra_client, has gra_client_id $id;
fetch { "id": $id };"""
                ).resolve()
                self.assertTrue(answer.is_concept_documents())
                docs = list(answer.as_concept_documents())
                self.assertEqual(len(docs), 2)
        finally:
            driver.close()

