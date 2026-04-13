from __future__ import annotations

import unittest
from dataclasses import replace

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.database_lifecycle import layer_a_db_name
from rpa_plugin_skill.core.openapi_registration_service import (
    expected_layer_a_db_for_registration,
    register_api_source,
)
from rpa_plugin_skill.core.typedb_bootstrap import connect_with_retry

SAMPLE_OPENAPI = """
openapi: 3.0.3
info:
  title: Financial Services API
  version: 1.0.0
components:
  schemas:
    Client:
      type: object
      required: [id, household_name]
      properties:
        id: { type: integer }
        household_name: { type: string }
    InsurancePolicy:
      type: object
      required: [id, client_id, policy_type]
      properties:
        id: { type: integer }
        client_id: { type: integer }
        policy_type: { type: string }
paths:
  /clients:
    get:
      operationId: listClients
      responses:
        "200": { description: ok }
  /insurance-policies:
    get:
      operationId: listInsurancePolicies
      parameters:
        - name: status
          in: query
          schema: { type: string }
      responses:
        "200": { description: ok }
"""


class ApiRegistrationServiceUnitTests(unittest.TestCase):
    def test_expected_layer_a_db_matches_lifecycle_mapping(self) -> None:
        cfg = AppConfig.from_env()
        reg_id = "api-financial-main"
        self.assertEqual(
            expected_layer_a_db_for_registration(cfg, reg_id),
            layer_a_db_name(cfg, reg_id),
        )


class ApiRegistrationServiceIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        base = AppConfig.from_env()
        self.cfg = replace(base, typedb_connect_retries=1, typedb_connect_retry_delay_sec=0.1)
        try:
            driver = connect_with_retry(self.cfg)
            driver.close()
        except Exception:
            self.skipTest("TypeDB not available for OpenAPI registration integration test")

    def tearDown(self) -> None:
        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            return
        try:
            for reg_id in ("api-financial-alpha", "api-financial-beta"):
                db_name = layer_a_db_name(self.cfg, reg_id)
                if driver.databases.contains(db_name):
                    driver.databases.get(db_name).delete()
        finally:
            driver.close()

    def test_api_registrations_map_to_distinct_layer_a_dbs_with_preview(self) -> None:
        first = register_api_source(
            config=self.cfg,
            source_name="Financial Alpha",
            spec_source=SAMPLE_OPENAPI,
            source_url="http://alpha/v1",
            registration_id="api-financial-alpha",
        )
        second = register_api_source(
            config=self.cfg,
            source_name="Financial Beta",
            spec_source=SAMPLE_OPENAPI,
            source_url="http://beta/v1",
            registration_id="api-financial-beta",
        )

        self.assertNotEqual(first.layer_a_db, second.layer_a_db)
        self.assertIn("Client", first.component_entities)
        self.assertIn("InsurancePolicy", first.component_entities)
        self.assertIn("/clients", first.path_templates)
        self.assertIn("/insurance-policies", first.path_templates)
        self.assertIn("listClients", first.extract_operations)
        self.assertIn("listInsurancePolicies", first.extract_operations)


if __name__ == "__main__":
    unittest.main()
