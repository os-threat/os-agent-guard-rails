# Manual test steps for SQL registration flow (issue #50)

This mirrors PLAN §5.1 expectations for SQL registration + schema preview + context switching.

## Prerequisites

- TypeDB reachable (`TYPEDB_ADDRESS`)
- `code/rpa_plugin_skill` dependencies installed

## Steps

1. Register first SQL source:

```bash
python -m rpa_plugin_skill \
  --register-sql-name "Medical Alpha" \
  --register-sql-ddl "CREATE TABLE doctors (id INT PRIMARY KEY, name VARCHAR(100));" \
  --register-sql-url "postgres://alpha"
```

Expected:

- prints registration id + Layer A database name
- prints table preview containing `doctors`
- writes source metadata into Layer C and sets active registration

2. Register second SQL source:

```bash
python -m rpa_plugin_skill \
  --register-sql-name "Medical Beta" \
  --register-sql-ddl "CREATE TABLE doctors (id INT PRIMARY KEY, name VARCHAR(100));" \
  --register-sql-url "postgres://beta"
```

Expected:

- second registration maps to a different Layer A DB name

3. List sources:

```bash
python -m rpa_plugin_skill --list-sources
```

Expected:

- both registrations appear in Layer C output

4. Switch active context:

```bash
python -m rpa_plugin_skill --activate-source sql-medical-beta
```

Expected:

- active registration setting updated in Layer C

5. Optional DB visibility check:

```bash
python -m rpa_plugin_skill --list-databases
```

Expected:

- Layer C, Layer B, and both Layer A databases appear
