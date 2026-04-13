# OpenAPI fetch and parse support (issue #51)

The API registration path accepts OpenAPI specs from inline text, file path, or URL.

## Auth modes for protected specs

`OpenAPIAuth` supports:

- `none` (default): no auth header
- `bearer`: `Authorization: Bearer <token>`
- `basic`: `Authorization: Basic <base64(username:password)>`

Manual paste mode is supported by passing inline JSON/YAML text directly to `load_openapi_text()` (no network call).

## Entry points

- `load_openapi_text(source, auth=None)`
  - URL fetch for `http(s)://...`
  - local file read for file paths
  - fallback: treat `source` as inline spec text
- `parse_openapi_document(text)`
  - parses JSON first, then YAML
  - validates minimum required structure:
    - `openapi` string
    - `info.title`
    - `paths` object

## Errors

- `OpenAPIFetchError`: fetch/auth mode failures
- `OpenAPIParseError`: invalid or structurally incomplete OpenAPI content
