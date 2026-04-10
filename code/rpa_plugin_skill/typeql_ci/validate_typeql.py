#!/usr/bin/env python3
"""
Run TypeQL fixtures against a live TypeDB 3.8+ server (schema / write / expected failures).

Normative language rules: ../../../skills/typedb/SKILL.md (semicolons, transaction types, roots).

Usage (with TypeDB listening on 127.0.0.1:1729 — see ../dev/docker-compose.yml):

  py -m venv .venv
  .venv\\Scripts\\activate
  pip install -r requirements.txt
  py validate_typeql.py

CI sets TYPEDB_ADDRESS (default 127.0.0.1:1729).
"""
from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path

from typedb.common.exception import TypeDBDriverException
from typedb.driver import Credentials, DriverOptions, TransactionType, TypeDB

FIXTURES = Path(__file__).resolve().parent / "fixtures"
DEFAULT_ADDRESS = os.environ.get("TYPEDB_ADDRESS", "127.0.0.1:1729")
DEFAULT_USER = os.environ.get("TYPEDB_USER", "admin")
DEFAULT_PASSWORD = os.environ.get("TYPEDB_PASSWORD", "password")
CONNECT_RETRIES = 45
CONNECT_DELAY_SEC = 2.0


def _connect_with_retry() -> TypeDB:
    creds = Credentials(DEFAULT_USER, DEFAULT_PASSWORD)
    opts = DriverOptions(is_tls_enabled=False)
    last: Exception | None = None
    for attempt in range(1, CONNECT_RETRIES + 1):
        try:
            driver = TypeDB.driver(DEFAULT_ADDRESS, creds, opts)
            driver.databases.all()
            return driver
        except Exception as e:  # noqa: BLE001 — surface any connection error
            last = e
            print(f"[validate_typeql] connect attempt {attempt}/{CONNECT_RETRIES} failed: {e}", file=sys.stderr)
            time.sleep(CONNECT_DELAY_SEC)
    raise RuntimeError(f"could not connect to TypeDB at {DEFAULT_ADDRESS}") from last


def _fresh_db(driver: TypeDB, prefix: str) -> str:
    name = f"{prefix}_{uuid.uuid4().hex[:12]}"
    if driver.databases.contains(name):
        driver.databases.delete(name)
    driver.databases.create(name)
    return name


def _run_schema(driver: TypeDB, db: str, tql: str) -> None:
    with driver.transaction(db, TransactionType.SCHEMA) as tx:
        tx.query(tql).resolve()
        tx.commit()


def _run_write(driver: TypeDB, db: str, tql: str) -> None:
    with driver.transaction(db, TransactionType.WRITE) as tx:
        tx.query(tql).resolve()
        tx.commit()


def main() -> int:
    schema_pass = sorted((FIXTURES / "schema_pass").glob("*.tql"))
    schema_fail = sorted((FIXTURES / "schema_fail").glob("*.tql"))
    write_pass = sorted((FIXTURES / "write_pass").glob("*.tql"))
    prelude = FIXTURES / "schema_pass" / "layer_a_minimal.tql"

    if not schema_pass or not schema_fail:
        print("Missing fixtures under schema_pass/ or schema_fail/", file=sys.stderr)
        return 1
    if write_pass and not prelude.is_file():
        print("write_pass/ requires schema_pass/layer_a_minimal.tql as prelude.", file=sys.stderr)
        return 1

    print(f"[validate_typeql] connecting to {DEFAULT_ADDRESS} ...")
    driver = _connect_with_retry()

    try:
        for path in schema_pass:
            text = path.read_text(encoding="utf-8").strip()
            db = _fresh_db(driver, "ok_schema")
            print(f"[validate_typeql] schema_pass {path.name} -> db {db}")
            _run_schema(driver, db, text)

        for path in schema_fail:
            text = path.read_text(encoding="utf-8").strip()
            db = _fresh_db(driver, "bad_schema")
            print(f"[validate_typeql] schema_fail {path.name} -> expect error (db {db})")
            try:
                _run_schema(driver, db, text)
            except TypeDBDriverException:
                continue
            print(
                f"[validate_typeql] FAIL: {path.name} was accepted but must be invalid TypeQL.",
                file=sys.stderr,
            )
            return 1

        prelude_text = prelude.read_text(encoding="utf-8").strip()
        for path in write_pass:
            text = path.read_text(encoding="utf-8").strip()
            db = _fresh_db(driver, "ok_write")
            print(f"[validate_typeql] write_pass {path.name} -> db {db}")
            _run_schema(driver, db, prelude_text)
            _run_write(driver, db, text)

    finally:
        driver.close()

    print("[validate_typeql] all checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
