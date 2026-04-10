from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    typedb_address: str
    typedb_user: str
    typedb_password: str
    layer_c_db: str
    layer_b_db: str
    layer_a_test_db: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            typedb_address=os.environ.get("TYPEDB_ADDRESS", "127.0.0.1:1729"),
            typedb_user=os.environ.get("TYPEDB_USER", "admin"),
            typedb_password=os.environ.get("TYPEDB_PASSWORD", "password"),
            layer_c_db=os.environ.get("LAYER_C_DB", "guardrails_layer_c"),
            layer_b_db=os.environ.get("LAYER_B_DB", "guardrails_layer_b"),
            layer_a_test_db=os.environ.get("LAYER_A_TEST_DB", "guardrails_layer_a_test"),
        )

    def database_names(self) -> list[str]:
        return [self.layer_c_db, self.layer_b_db, self.layer_a_test_db]
