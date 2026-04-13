# OpenAPI -> TypeQL transpiler and extract bundles (issue #52)

This module converts parsed OpenAPI docs into Layer A schema and extraction descriptors.

## Entry points

- `generate_define_from_openapi(doc, namespace="gra")`
  - Components schemas -> entities/attributes
  - Required fields -> plain `owns`
  - Optional fields -> `@card(0..1)`
  - Key strategy -> `id`/`uuid`/`external_id` gets `@key` when present
- `build_extract_bundles(doc)`
  - Paths/operations -> extract bundles with operation metadata
  - Includes parameter mapping placeholders by source (`path`, `query`, `header`, `cookie`)
- `apply_openapi_layer_a_schema(config, registration_id, openapi_doc)`
  - Applies generated `define` to the per-registration Layer A DB via schema transaction

## JSONPath / parameter mapping conventions

Each bundle includes:

- `source_pointer`: `paths.<path>.<method>`
- `response_jsonpath`: default `$.responses.200.body`
- `parameter_bindings`: map of parameter name -> `$.params.<in>.<name>`
  - examples:
    - path param `clientId` -> `$.params.path.clientId`
    - query param `limit` -> `$.params.query.limit`

These are mapping placeholders for sync worker execution logic in later tickets.

## Golden tests

- `tests/test_openapi_to_typeql.py`
- `tests/golden/openapi_to_typeql_sample.tql`
