from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen


class DDLParseError(ValueError):
    """Raised when a DDL statement is unsupported or invalid."""


@dataclass(frozen=True)
class ColumnDef:
    name: str
    sql_type: str
    nullable: bool = True
    default: str | None = None


@dataclass(frozen=True)
class ForeignKeyDef:
    columns: tuple[str, ...]
    ref_table: str
    ref_columns: tuple[str, ...]


@dataclass
class TableDef:
    name: str
    columns: list[ColumnDef] = field(default_factory=list)
    primary_key: tuple[str, ...] = ()
    foreign_keys: list[ForeignKeyDef] = field(default_factory=list)


@dataclass(frozen=True)
class DDLModel:
    tables: list[TableDef]


def load_ddl_text(source: str) -> str:
    """Load DDL text from inline string, file path, or HTTP(S) URL."""
    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"}:
        with urlopen(source) as response:  # nosec B310 - controlled use for explicit user input
            return response.read().decode("utf-8")

    path = Path(source)
    if path.exists() and path.is_file():
        return path.read_text(encoding="utf-8")

    return source


def parse_postgres_ddl(ddl_text: str) -> DDLModel:
    cleaned = _strip_comments(ddl_text)
    _reject_unsupported_statements(cleaned)

    table_matches = list(
        re.finditer(
            r"CREATE\s+TABLE\s+([\w\"\.]+)\s*\((.*?)\)\s*;",
            cleaned,
            flags=re.IGNORECASE | re.DOTALL,
        )
    )
    if not table_matches:
        raise DDLParseError("No supported CREATE TABLE statements found in DDL input")

    tables: list[TableDef] = []
    for match in table_matches:
        table_name = _normalize_ident(match.group(1))
        body = match.group(2)
        table = TableDef(name=table_name)
        parts = _split_top_level_commas(body)

        for raw_part in parts:
            part = raw_part.strip()
            if not part:
                continue

            upper = part.upper()
            if upper.startswith("PRIMARY KEY"):
                table.primary_key = _parse_primary_key(part)
                continue
            if upper.startswith("FOREIGN KEY"):
                table.foreign_keys.append(_parse_foreign_key(part))
                continue
            if upper.startswith("CONSTRAINT"):
                constraint_body = part.split(None, 2)[2] if len(part.split(None, 2)) == 3 else ""
                constraint_upper = constraint_body.upper()
                if constraint_upper.startswith("PRIMARY KEY"):
                    table.primary_key = _parse_primary_key(constraint_body)
                    continue
                if constraint_upper.startswith("FOREIGN KEY"):
                    table.foreign_keys.append(_parse_foreign_key(constraint_body))
                    continue
                raise DDLParseError(f"Unsupported table constraint: {part}")

            column, fk = _parse_column(part)
            table.columns.append(column)
            if fk:
                table.foreign_keys.append(fk)
            if "PRIMARY KEY" in upper and not table.primary_key:
                table.primary_key = (column.name,)

        if not table.columns:
            raise DDLParseError(f"Table '{table_name}' has no parsable columns")
        tables.append(table)

    return DDLModel(tables=tables)


def _strip_comments(text: str) -> str:
    return re.sub(r"--.*?$", "", text, flags=re.MULTILINE)


def _reject_unsupported_statements(ddl_text: str) -> None:
    unsupported = [
        r"\bALTER\s+TABLE\b",
        r"\bCREATE\s+INDEX\b",
        r"\bCREATE\s+VIEW\b",
        r"\bCREATE\s+TYPE\b",
        r"\bDROP\s+TABLE\b",
    ]
    for pattern in unsupported:
        if re.search(pattern, ddl_text, flags=re.IGNORECASE):
            label = pattern.replace("\\b", "")
            raise DDLParseError(f"Unsupported DDL statement detected: {label}")


def _split_top_level_commas(block: str) -> list[str]:
    items: list[str] = []
    depth = 0
    start = 0
    for i, char in enumerate(block):
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(depth - 1, 0)
        elif char == "," and depth == 0:
            items.append(block[start:i])
            start = i + 1
    items.append(block[start:])
    return items


def _normalize_ident(token: str) -> str:
    return token.strip().strip('"')


def _parse_column(part: str) -> tuple[ColumnDef, ForeignKeyDef | None]:
    match = re.match(r'^\s*([\w\"]+)\s+(.+)$', part, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise DDLParseError(f"Could not parse column definition: {part}")

    name = _normalize_ident(match.group(1))
    remainder = match.group(2).strip()
    parts = remainder.split()
    if not parts:
        raise DDLParseError(f"Missing SQL type for column: {name}")

    sql_type = _extract_type(remainder)
    upper = remainder.upper()
    nullable = "NOT NULL" not in upper and "PRIMARY KEY" not in upper

    default_match = re.search(r"\bDEFAULT\b\s+([^\s,]+)", remainder, flags=re.IGNORECASE)
    default = default_match.group(1) if default_match else None

    fk: ForeignKeyDef | None = None
    ref_match = re.search(
        r"REFERENCES\s+([\w\"\.]+)\s*\(([^\)]+)\)", remainder, flags=re.IGNORECASE
    )
    if ref_match:
        fk = ForeignKeyDef(
            columns=(name,),
            ref_table=_normalize_ident(ref_match.group(1)),
            ref_columns=tuple(_normalize_ident(c.strip()) for c in ref_match.group(2).split(",")),
        )

    return ColumnDef(name=name, sql_type=sql_type, nullable=nullable, default=default), fk


def _extract_type(remainder: str) -> str:
    stop_keywords = [
        "NOT NULL",
        "NULL",
        "DEFAULT",
        "PRIMARY KEY",
        "REFERENCES",
        "UNIQUE",
        "CHECK",
    ]
    upper = remainder.upper()
    cut = len(remainder)
    for keyword in stop_keywords:
        idx = upper.find(keyword)
        if idx != -1:
            cut = min(cut, idx)
    sql_type = remainder[:cut].strip().rstrip(",")
    if not sql_type:
        raise DDLParseError(f"Could not determine SQL type from segment: {remainder}")
    return sql_type


def _parse_primary_key(text: str) -> tuple[str, ...]:
    match = re.search(r"PRIMARY\s+KEY\s*\(([^\)]+)\)", text, flags=re.IGNORECASE)
    if not match:
        raise DDLParseError(f"Invalid PRIMARY KEY clause: {text}")
    return tuple(_normalize_ident(c.strip()) for c in match.group(1).split(","))


def _parse_foreign_key(text: str) -> ForeignKeyDef:
    match = re.search(
        r"FOREIGN\s+KEY\s*\(([^\)]+)\)\s+REFERENCES\s+([\w\"\.]+)\s*\(([^\)]+)\)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        raise DDLParseError(f"Invalid FOREIGN KEY clause: {text}")

    return ForeignKeyDef(
        columns=tuple(_normalize_ident(c.strip()) for c in match.group(1).split(",")),
        ref_table=_normalize_ident(match.group(2)),
        ref_columns=tuple(_normalize_ident(c.strip()) for c in match.group(3).split(",")),
    )
