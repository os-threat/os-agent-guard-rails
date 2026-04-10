from __future__ import annotations

import argparse

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.typedb_bootstrap import bootstrap_databases


def main() -> int:
    parser = argparse.ArgumentParser(description="RPA plugin/skill skeleton")
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Create missing Layer C/B/test Layer A databases on the configured TypeDB instance.",
    )
    args = parser.parse_args()

    config = AppConfig.from_env()
    print(f"[rpa_plugin_skill] TypeDB address: {config.typedb_address}")
    print(
        "[rpa_plugin_skill] Database targets: "
        f"C={config.layer_c_db}, B={config.layer_b_db}, A_test={config.layer_a_test_db}"
    )

    if args.bootstrap:
        created = bootstrap_databases(config)
        if created:
            print(f"[rpa_plugin_skill] Created databases: {', '.join(created)}")
        else:
            print("[rpa_plugin_skill] All target databases already exist.")

    print("[rpa_plugin_skill] Skeleton startup complete.")
    return 0
