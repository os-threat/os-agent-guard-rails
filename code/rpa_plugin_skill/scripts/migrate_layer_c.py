from __future__ import annotations

from rpa_plugin_skill.core.config import AppConfig
from rpa_plugin_skill.core.layer_c_migrations import apply_layer_c_migrations


def main() -> int:
    config = AppConfig.from_env()
    applied = apply_layer_c_migrations(config)
    if applied:
        print(f"[layer_c_migrate] Applied migrations: {', '.join(applied)}")
    else:
        print("[layer_c_migrate] No pending migrations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
