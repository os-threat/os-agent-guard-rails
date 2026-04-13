# SQL DDL ingestion support (issue #48)

The SQL registration path accepts PostgreSQL-oriented DDL via inline text, local file path, or URL.

## Supported subset

The parser currently supports a pragmatic subset needed for schema registration:

- `CREATE TABLE ... ( ... );`
- Column definitions with:
  - SQL types (including parameterized forms like `VARCHAR(255)`, `NUMERIC(12,2)`)
  - `NOT NULL`
  - `DEFAULT <value>`
  - inline `PRIMARY KEY`
  - inline `REFERENCES ...(...)`
- Table constraints:
  - `PRIMARY KEY (...)`
  - `FOREIGN KEY (...) REFERENCES ...(...)`
  - `CONSTRAINT <name> PRIMARY KEY (...)`
  - `CONSTRAINT <name> FOREIGN KEY (...) REFERENCES ...(...)`

## Currently unsupported (explicit error)

The parser raises `DDLParseError` when these statements are detected:

- `ALTER TABLE`
- `CREATE INDEX`
- `CREATE VIEW`
- `CREATE TYPE`
- `DROP TABLE`

These can be added in later tickets as the SQL transpiler matures.

## Entry points

- `load_ddl_text(source: str) -> str`
  - if `source` is `http(s)://...`, fetches URL
  - if `source` is a file path, reads file
  - otherwise treats input as inline DDL
- `parse_postgres_ddl(ddl_text: str) -> DDLModel`

## Internal model

`DDLModel` -> list of `TableDef` containing:

- table name
- columns (`ColumnDef`)
- primary key columns
- foreign keys (`ForeignKeyDef`)

This model is the input to the SQL -> TypeQL transpiler path in the next ticket.
