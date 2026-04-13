from __future__ import annotations

import os
import unittest
import uuid

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.layer_c_store import (
    LayerCStore,
    RegisteredSourceInput,
    SecretReferenceError,
)
from rpa_plugin_skill.core.typedb_bootstrap import connect_with_retry


class LayerCStoreValidationTests(unittest.TestCase):
    def test_rejects_plaintext_secret(self) -> None:
        cfg = AppConfig.from_env()
        store = LayerCStore(cfg, ensure_schema=False)

        with self.assertRaises(SecretReferenceError):
            store.upsert_registered_source(
                RegisteredSourceInput(
                    registration_id="reg-plain",
                    source_name="Plain Source",
                    source_kind="sql",
                    source_url="postgres://localhost/db",
                    source_description="test",
                    source_is_active=True,
                    credential_ref_id="cred-plain",
                    secret_provider="vault",
                    secret_ref="super-secret-password",
                )
            )


class LayerCStoreIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.test_suffix = uuid.uuid4().hex[:8]
        self.cfg = AppConfig(
            typedb_address=os.environ.get("TYPEDB_ADDRESS", "127.0.0.1:1729"),
            typedb_user=os.environ.get("TYPEDB_USER", "admin"),
            typedb_password=os.environ.get("TYPEDB_PASSWORD", "password"),
            typedb_tls_enabled=False,
            typedb_connect_retries=1,
            typedb_connect_retry_delay_sec=0.1,
            layer_c_db=f"layer_c_store_test_{self.test_suffix}",
            layer_b_db=f"layer_b_store_test_{self.test_suffix}",
            layer_a_test_db=f"layer_a_store_test_{self.test_suffix}",
            layer_a_prefix="guardrails_layer_a_",
            max_database_name_length=64,
        )

        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            self.skipTest("TypeDB not available for integration test")

        driver.databases.create(self.cfg.layer_c_db)
        driver.databases.create(self.cfg.layer_b_db)
        driver.close()

    def tearDown(self) -> None:
        try:
            driver = connect_with_retry(self.cfg)
        except Exception:
            return

        for db_name in (self.cfg.layer_c_db, self.cfg.layer_b_db):
            if driver.databases.contains(db_name):
                driver.databases.get(db_name).delete()
        driver.close()

    def test_upsert_and_fetch_source_with_secret_reference(self) -> None:
        store = LayerCStore(self.cfg, ensure_schema=True)
        store.upsert_registered_source(
            RegisteredSourceInput(
                registration_id="reg-1",
                source_name="Medical SQL",
                source_kind="sql",
                source_url="postgres://medical",
                source_description="medical source",
                source_is_active=True,
                credential_ref_id="cred-1",
                secret_provider="vault",
                secret_ref="vault://prod/medical/sql-creds",
            )
        )

        docs = store.fetch_registered_sources()
        self.assertEqual(len(docs), 1)
        rendered = str(docs[0])
        self.assertIn("reg-1", rendered)
        self.assertIn("Medical SQL", rendered)


if __name__ == "__main__":
    unittest.main()
