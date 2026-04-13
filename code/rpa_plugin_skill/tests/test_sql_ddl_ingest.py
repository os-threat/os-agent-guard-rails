from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rpa_plugin_skill.core.sql_ddl_ingest import DDLParseError, load_ddl_text, parse_postgres_ddl

SAMPLE_DDL = """
CREATE TABLE patients (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE prescriptions (
    id INT PRIMARY KEY,
    patient_id INT REFERENCES patients(id),
    doctor_id INT,
    CONSTRAINT fk_presc_patient FOREIGN KEY (patient_id) REFERENCES patients(id)
);
"""


class SqlDdlIngestTests(unittest.TestCase):
    def test_parse_supported_create_table_subset(self) -> None:
        model = parse_postgres_ddl(SAMPLE_DDL)
        self.assertEqual(len(model.tables), 2)

        patients = model.tables[0]
        self.assertEqual(patients.name, "patients")
        self.assertEqual(patients.primary_key, ("id",))
        self.assertEqual(patients.columns[1].name, "name")
        self.assertFalse(patients.columns[1].nullable)

        prescriptions = model.tables[1]
        self.assertEqual(prescriptions.name, "prescriptions")
        self.assertGreaterEqual(len(prescriptions.foreign_keys), 1)

    def test_reject_unsupported_alter_table(self) -> None:
        ddl = SAMPLE_DDL + "\nALTER TABLE patients ADD COLUMN legacy_code TEXT;"
        with self.assertRaises(DDLParseError):
            parse_postgres_ddl(ddl)

    def test_load_from_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "schema.sql"
            path.write_text(SAMPLE_DDL, encoding="utf-8")
            loaded = load_ddl_text(str(path))
            self.assertIn("CREATE TABLE patients", loaded)

    def test_invalid_clause_reports_clear_error(self) -> None:
        bad = "CREATE TABLE t (CONSTRAINT c UNIQUE (name));"
        with self.assertRaises(DDLParseError) as ctx:
            parse_postgres_ddl(bad)
        self.assertIn("Unsupported table constraint", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
