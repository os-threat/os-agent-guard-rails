from __future__ import annotations

import os
import unittest

from rpa_plugin_skill.core.config import AppConfig
from scripts.migrate_layer_c import _schema_contains_marker


class LayerCMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        for key in ("LAYER_C_DB",):
            os.environ.pop(key, None)

    def test_marker_detection(self) -> None:
        schema = "define\n  entity gr_registered_source;"
        self.assertTrue(_schema_contains_marker(schema, "gr_registered_source"))
        self.assertFalse(_schema_contains_marker(schema, "gr_task_definition"))

    def test_config_layer_c_name_default(self) -> None:
        cfg = AppConfig.from_env()
        self.assertEqual(cfg.layer_c_db, "guardrails_layer_c")


if __name__ == "__main__":
    unittest.main()
