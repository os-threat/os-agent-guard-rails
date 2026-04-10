from __future__ import annotations

import argparse

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.health import probe_typedb
from rpa_plugin_skill.core.typedb_bootstrap import bootstrap_databases


def main() -> int:
    parser = argparse.ArgumentParser(description="RPA plugin/skill skeleton")
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Create missing Layer C/B/test Layer A databases on the configured TypeDB instance.",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Probe TypeDB connectivity for UI/workers and print a machine-readable status line.",
    )
    args = parser.parse_args()

    config = AppConfig.from_env()
    print(f"[rpa_plugin_skill] TypeDB address: {config.typedb_address}")
    print(
        "[rpa_plugin_skill] Database targets: "
        f"C={config.layer_c_db}, B={config.layer_b_db}, A_test={config.layer_a_test_db}"
    )

    if args.health:
        result = probe_typedb(config)
        if result.ok:
            print(
                f"[rpa_plugin_skill] HEALTH_OK address={result.address} "
                f"database_count={result.database_count}"
            )
        else:
            print(
                f"[rpa_plugin_skill] HEALTH_FAIL address={result.address} "
                f"error={result.error}"
            )
            return 1

    if args.bootstrap:
        created = bootstrap_databases(config)
        if created:
            print(f"[rpa_plugin_skill] Created databases: {', '.join(created)}")
        else:
            print("[rpa_plugin_skill] All target databases already exist.")

    print("[rpa_plugin_skill] Skeleton startup complete.")
    return 0
