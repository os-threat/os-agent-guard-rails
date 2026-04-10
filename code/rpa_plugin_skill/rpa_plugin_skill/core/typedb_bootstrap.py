from __future__ import annotations

from typedb.driver import Credentials, DriverOptions, TypeDB

from .config import AppConfig


def connect(config: AppConfig) -> TypeDB:
    credentials = Credentials(config.typedb_user, config.typedb_password)
    options = DriverOptions(is_tls_enabled=False)
    return TypeDB.driver(config.typedb_address, credentials, options)


def bootstrap_databases(config: AppConfig) -> list[str]:
    created: list[str] = []
    driver = connect(config)
    try:
        for name in config.database_names():
            if not driver.databases.contains(name):
                driver.databases.create(name)
                created.append(name)
    finally:
        driver.close()
    return created
