# Manual task ready-to-schedule check (issue #67)

From `code/rpa_plugin_skill`:

```bash
python -m rpa_plugin_skill --register-sql-name "Medical Alpha" --register-sql-ddl "CREATE TABLE clients (id INT PRIMARY KEY, status VARCHAR(30));" --register-sql-url "postgresql://medical_app:medical_app_dev_pw@localhost:5433/medical_mini_app"
python -m rpa_plugin_skill --task-prepare-load --task-source sql-medical-alpha --task-id task-001 --task-name "Client extraction" --task-description "Extract clients and validate status before review"
```

Expected:

- output line starts with `[rpa_plugin_skill] TASK_READY_TO_SCHEDULE`
- includes:
  - `status=ready`
  - `rows_loaded=<non-negative count>`
  - `plan=` JSON summary of SQL/API extraction plan
- task metadata in Layer C now has:
  - `gr_task_status = ready`
  - `gr_extract_plan_ref` populated for scheduler preview
