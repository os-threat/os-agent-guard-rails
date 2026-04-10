from __future__ import annotations

import os
import unittest

from rpa_plugin_skill.core.config import AppConfig


class AppConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.keys = (
            "TYPEDB_ADDRESS",
            "TYPEDB_USER",
            "TYPEDB_PASSWORD",
            "TYPEDB_TLS_ENABLED",
            "TYPEDB_CONNECT_RETRIES",
            "TYPEDB_CONNECT_RETRY_DELAY_SEC",
            "LAYER_C_DB",
            "LAYER_B_DB",
            "LAYER_A_TEST_DB",
        )
        for key in self.keys:
            os.environ.pop(key, None)

    def test_defaults(self) -> None:
        cfg = AppConfig.from_env()
        self.assertEqual(cfg.typedb_address, "127.0.0.1:1729")
        self.assertFalse(cfg.typedb_tls_enabled)
        self.assertEqual(cfg.typedb_connect_retries, 5)
        self.assertEqual(cfg.typedb_connect_retry_delay_sec, 1.0)
        self.assertEqual(cfg.layer_c_db, "guardrails_layer_c")
        self.assertEqual(cfg.layer_b_db, "guardrails_layer_b")
        self.assertEqual(cfg.layer_a_test_db, "guardrails_layer_a_test")

    def test_overrides(self) -> None:
        os.environ["TYPEDB_ADDRESS"] = "10.0.0.10:1729"
        os.environ["TYPEDB_TLS_ENABLED"] = "true"
        os.environ["TYPEDB_CONNECT_RETRIES"] = "9"
        os.environ["TYPEDB_CONNECT_RETRY_DELAY_SEC"] = "0.2"
        os.environ["LAYER_C_DB"] = "custom_c"
        os.environ["LAYER_B_DB"] = "custom_b"
        os.environ["LAYER_A_TEST_DB"] = "custom_a"

        cfg = AppConfig.from_env()
        self.assertEqual(cfg.typedb_address, "10.0.0.10:1729")
        self.assertTrue(cfg.typedb_tls_enabled)
        self.assertEqual(cfg.typedb_connect_retries, 9)
        self.assertEqual(cfg.typedb_connect_retry_delay_sec, 0.2)
        self.assertEqual(cfg.database_names(), ["custom_c", "custom_b", "custom_a"])


if __name__ == "__main__":
    unittest.main()
