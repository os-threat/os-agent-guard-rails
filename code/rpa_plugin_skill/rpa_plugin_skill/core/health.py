from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig
from .typedb_bootstrap import connect_with_retry


@dataclass(frozen=True)
class HealthProbeResult:
    ok: bool
    address: str
    database_count: int
    error: str | None = None


def probe_typedb(config: AppConfig) -> HealthProbeResult:
    try:
        driver = connect_with_retry(config)
    except Exception as exc:  # noqa: BLE001
        return HealthProbeResult(
            ok=False,
            address=config.typedb_address,
            database_count=0,
            error=str(exc),
        )

    try:
        databases = list(driver.databases.all())
        return HealthProbeResult(
            ok=True,
            address=config.typedb_address,
            database_count=len(databases),
            error=None,
        )
    finally:
        driver.close()

