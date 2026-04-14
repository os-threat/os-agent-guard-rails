# Manual task composer check (issue #66)

From `code/rpa_plugin_skill`:

```bash
python -m rpa_plugin_skill --register-sql-name "Medical Alpha" --register-sql-ddl "CREATE TABLE clients (id INT PRIMARY KEY, status VARCHAR(30));" --register-sql-url "postgres://alpha"
python -m rpa_plugin_skill --task-compose-preview --task-source sql-medical-alpha --task-description "Extract clients, validate status, and schedule review tasks"
```

Expected:

- output line starts with `[rpa_plugin_skill] TASK_COMPOSER`
- payload contains:
  - `description_left` with original text
  - `layer_a_db` mapped from `sql-medical-alpha`
  - `schema_highlights` including labels aligned to Layer A schema (for example `gra_client`)
  - `process_highlights` including `extract`, `validate`, `schedule`
  - `flow_chart_right.diagram_mermaid` with schema objects and process logic nodes
  - `flow_chart_right.steps` containing ordered flow entries for execution/assessment path
