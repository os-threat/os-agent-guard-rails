from __future__ import annotations

import time

from typedb.driver import Credentials, DriverOptions, TypeDB

from .config import AppConfig


def connect_with_retry(config: AppConfig) -> TypeDB:
    credentials = Credentials(config.typedb_user, config.typedb_password)
    options = DriverOptions(is_tls_enabled=config.typedb_tls_enabled)
    last_error: Exception | None = None

    for attempt in range(1, config.typedb_connect_retries + 1):
        try:
            driver = TypeDB.driver(config.typedb_address, credentials, options)
            driver.databases.all()
            return driver
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == config.typedb_connect_retries:
                break
            time.sleep(config.typedb_connect_retry_delay_sec)

    message = (
        "Failed to connect to TypeDB at "
        f"{config.typedb_address} after {config.typedb_connect_retries} attempts"
    )
    raise RuntimeError(message) from last_error
