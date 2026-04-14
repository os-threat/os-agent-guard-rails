# Task Composer UI contract (issue #66)

Implements PLAN §5.5:

- left pane: task description
- right pane: schema-aware flow chart
- highlights object names and process logic from the active registration's Layer A schema

## Preview contract

CLI: `--task-compose-preview --task-source <REG_ID> --task-description "<text>"`

Returns JSON payload:

- `description_left`: original task description text
- `flow_chart_right.diagram_mermaid`: Mermaid flow chart for the task
- `flow_chart_right.steps`: ordered execution steps
- `schema_highlights`: matched schema labels (`entity`, `attribute`, `relation`)
- `process_highlights`: matched process keywords (extract/validate/schedule/etc.)
- `layer_a_db`: registration-scoped Layer A database name

## Behavior

1. Resolve Layer A DB name for the selected registration.
2. Read Layer A schema text.
3. Match schema labels present in task description.
4. Match process terms from known task operation keywords.
5. Build right-pane flow chart + ordered step list for UI rendering.
