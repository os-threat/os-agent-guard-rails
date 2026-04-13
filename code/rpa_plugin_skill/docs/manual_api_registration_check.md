# Manual OpenAPI registration check (issue #53)

From `code/rpa_plugin_skill`:

```bash
python -m rpa_plugin_skill --bootstrap
python -m rpa_plugin_skill --register-api-name "Financial Main" --register-api-spec "../../plan/financial_planner_api_scenario/openapi/financial-services.yaml" --register-api-url "http://localhost:4010/v1"
python -m rpa_plugin_skill --list-sources
```

Expected:

- registration id defaults to `api-financial-main`
- a deterministic Layer A DB is created for that id
- preview output includes:
  - `components=` list of OpenAPI schemas
  - `paths=` list including financial scenario route families (`/clients`, `/households`, `/insurance-policies`, `/tasks`, `/communications`)
  - `extract_ops=` operation ids from OpenAPI paths
- Layer C setting `active_registration_id` switches to the API registration
