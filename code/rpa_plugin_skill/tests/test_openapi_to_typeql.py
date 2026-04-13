from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.database_lifecycle import layer_a_db_name
from rpa_plugin_skill.core.openapi_to_typeql import (
    apply_openapi_layer_a_schema,
    build_extract_bundles,
    generate_define_from_openapi,
)
from rpa_plugin_skill.core.typedb_bootstrap import connect_with_retry

OPENAPI_FRAGMENT = {
    "openapi": "3.0.3",
    "info": {"title": "Financial API", "version": "1.0.0"},
    "components": {
        "schemas": {
            "Client": {
                "type": "object",
                "required": ["id", "household_name"],
                "properties": {
                    "id": {"type": "integer"},
                    "household_name": {"type": "string"},
                    "state_of_residence": {"type": "string"},
                },
            },
            "PlanRecommendation": {
                "type": "object",
                "required": ["id", "client_id", "status"],
                "properties": {
                    "id": {"type": "integer"},
                    "client_id": {"type": "integer"},
                    "status": {"type": "string"},
                },
            },
        }
    },
    "paths": {
        "/clients": {
            "get": {
                "operationId": "listClients",
                "parameters": [
                    {"name": "limit", "in": "query", "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"description": "ok"}},
            }
        },
        "/clients/{clientId}/recommendations": {
            "get": {
                "operationId": "listRecommendations",
                "parameters": [
                    {
                        "name": "clientId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                    }
                ],
                "responses": {"200": {"description": "ok"}},
            }
        },
    },
}


class OpenApiToTypeqlTests(unittest.TestCase):
    def test_generate_matches_golden_fragment(self) -> None:
        generated = generate_define_from_openapi(OPENAPI_FRAGMENT, namespace="gra")
        golden = (Path(__file__).parent / "golden" / "openapi_to_typeql_sample.tql").read_text(
            encoding="utf-8"
        )
        self.assertEqual(generated.strip(), golden.strip())

    def test_extract_bundles_include_parameter_mappings(self) -> None:
        bundles = build_extract_bundles(OPENAPI_FRAGMENT)
        self.assertEqual(len(bundles), 2)

        by_operation = {b.operation_id: b for b in bundles}
        self.assertIn("listClients", by_operation)
        self.assertEqual(
            by_operation["listClients"].parameter_bindings["limit"],
            "$.params.query.limit",
        )
        self.assertEqual(
            by_operation["listRecommendations"].parameter_bindings["clientId"],
            "$.params.path.clientId",
        )


class OpenApiToTypeqlIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        base = AppConfig.from_env()
        self.cfg = replace(base, typedb_connect_retries=1, typedb_connect_retry_delay_sec=0.1)
        try:
            driver = connect_with_retry(self.cfg)
            driver.close()
        except Exception:
            self.skipTest("TypeDB not available for OpenAPI schema integration test")

    def tearDown(self) -> None:
        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            return
        try:
            db_name = layer_a_db_name(self.cfg, "openapi-financial-main")
            if driver.databases.contains(db_name):
                driver.databases.get(db_name).delete()
        finally:
            driver.close()

    def test_apply_schema_targets_named_layer_a_db(self) -> None:
        db_name = apply_openapi_layer_a_schema(self.cfg, "openapi-financial-main", OPENAPI_FRAGMENT)
        expected = layer_a_db_name(self.cfg, "openapi-financial-main")
        self.assertEqual(db_name, expected)

        driver = connect_with_retry(self.cfg)
        try:
            schema = driver.databases.get(expected).schema()
            self.assertIn("entity gra_client", schema)
            self.assertIn("owns gra_client_id @key", schema)
        finally:
            driver.close()


if __name__ == "__main__":
    unittest.main()
