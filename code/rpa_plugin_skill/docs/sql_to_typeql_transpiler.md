# SQL -> TypeQL schema transpiler (issue #49)

This module converts parsed Postgres DDL (`DDLModel`) into TypeQL schema text for Layer A databases.

## Entry points

- `generate_define_from_ddl(model, namespace="gra") -> str`
  - emits a complete `define` query
  - uses TypeDB 3.x roots (`entity`, `relation`, `attribute`)
  - assigns stable keys with `@key`
- `apply_layer_a_schema(config, registration_id, define_query, redefine=False)`
  - resolves named Layer A DB from registration id
  - opens a `schema` transaction against that database
  - applies `define` or `redefine`

## Key strategy

- Single-column SQL PK -> corresponding attribute gets `@key`
- Composite SQL PK -> synthetic attribute `<entity>_composite_key` gets `@key`

## SQL -> TypeQL value mapping

- `int`, `serial`, `bigint` -> `integer`
- `numeric`, `decimal` -> `decimal`
- `double`, `real`, `float` -> `double`
- `boolean` -> `boolean`
- `timestamp` -> `datetime`
- `date` -> `date`
- fallback -> `string`

## Foreign keys

Each FK creates a relation:

- relation label: `<namespace>_<from>_to_<to>_fk_<n>`
- roles: `<from>_row`, `<to>_row`
- source and target entities `play` corresponding roles

## Golden tests

See:

- `tests/test_sql_to_typeql.py`
- `tests/golden/sql_to_typeql_sample.tql`
