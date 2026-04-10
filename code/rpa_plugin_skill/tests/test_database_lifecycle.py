from __future__ import annotations

import unittest

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.database_lifecycle import layer_a_db_name


class DatabaseLifecycleNamingTests(unittest.TestCase):
    def test_layer_a_name_is_deterministic(self) -> None:
        cfg = AppConfig.from_env()
        first = layer_a_db_name(cfg, "Medical App Prod")
        second = layer_a_db_name(cfg, "Medical App Prod")
        self.assertEqual(first, second)

    def test_layer_a_name_sanitizes_and_limits_length(self) -> None:
        cfg = AppConfig.from_env()
        cfg = AppConfig(
            typedb_address=cfg.typedb_address,
            typedb_user=cfg.typedb_user,
            typedb_password=cfg.typedb_password,
            typedb_tls_enabled=cfg.typedb_tls_enabled,
            typedb_connect_retries=cfg.typedb_connect_retries,
            typedb_connect_retry_delay_sec=cfg.typedb_connect_retry_delay_sec,
            layer_c_db=cfg.layer_c_db,
            layer_b_db=cfg.layer_b_db,
            layer_a_test_db=cfg.layer_a_test_db,
            layer_a_prefix="ga_",
            max_database_name_length=24,
        )
        name = layer_a_db_name(cfg, "API://Accounts+Planner=North")
        self.assertTrue(name.startswith("ga_"))
        self.assertLessEqual(len(name), 24)


if __name__ == "__main__":
    unittest.main()
