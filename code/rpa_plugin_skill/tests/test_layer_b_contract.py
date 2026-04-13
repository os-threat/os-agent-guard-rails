from __future__ import annotations

import unittest

from scripts.check_layer_b_contract import _ephemeral_config


class LayerBContractScriptTests(unittest.TestCase):
    def test_ephemeral_db_names_are_distinct(self) -> None:
        cfg = _ephemeral_config()
        self.assertNotEqual(cfg.layer_c_db, cfg.layer_b_db)
        self.assertIn("layer_b_contract_", cfg.layer_b_db)


if __name__ == "__main__":
    unittest.main()
