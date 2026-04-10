from __future__ import annotations

import os
import unittest

from rpa_plugin_skill.core.config import AppConfig


class AppConfigTests(unittest.TestCase):
    def test_defaults(self) -> None:
        for key in (
            "TYPEDB_ADDRESS",
            "TYPEDB_USER",
            "TYPEDB_PASSWORD",
            "LAYER_C_DB",
            "LAYER_B_DB",
            "LAYER_A_TEST_DB",
        ):
            os.environ.pop(key, None)

        cfg = AppConfig.from_env()
        self.assertEqual(cfg.typedb_address, "127.0.0.1:1729")
        self.assertEqual(cfg.layer_c_db, "guardrails_layer_c")
        self.assertEqual(cfg.layer_b_db, "guardrails_layer_b")
        self.assertEqual(cfg.layer_a_test_db, "guardrails_layer_a_test")

    def test_overrides(self) -> None:
        os.environ["TYPEDB_ADDRESS"] = "10.0.0.10:1729"
        os.environ["LAYER_C_DB"] = "custom_c"
        os.environ["LAYER_B_DB"] = "custom_b"
        os.environ["LAYER_A_TEST_DB"] = "custom_a"

        cfg = AppConfig.from_env()
        self.assertEqual(cfg.typedb_address, "10.0.0.10:1729")
        self.assertEqual(cfg.database_names(), ["custom_c", "custom_b", "custom_a"])


if __name__ == "__main__":
    unittest.main()
