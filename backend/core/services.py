"""Service helpers for QueryMind."""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
from time import perf_counter
from typing import Any

from django.db import connection
from django.db.utils import DatabaseError

from .nl2sql import NL2SQLAgent, UnsafeQueryError, serialize_schema


EXCLUDED_SCHEMA_TABLES = {
    "django_migrations",
    "django_content_type",
    "django_admin_log",
    "auth_permission",
    "auth_group",
    "auth_group_permissions",
    "auth_user",
    "auth_user_groups",
    "auth_user_user_permissions",
    "django_session",
}

EXCLUDED_INSERT_TABLES = {
    "query_log",
    "etl_log",
}

GRAPH_MODE_TABLES = {
    "academic": {
        "department",
        "person",
        "student",
        "faculty",
        "semester",
        "course",
        "course_prerequisite",
        "section",
        "enrollment",
        "assessment",
        "exam",
        "exam_result",
        "assignment",
        "assignment_submission",
    },
    "finance": {
        "student",
        "semester",
        "fee_invoice",
        "fee_payment",
        "department",
    },
    "housing": {
        "student",
        "semester",
        "hostel",
        "hostel_room",
        "hostel_allotment",
        "department",
    },
}


@dataclass(slots=True)
class SchemaRelationship:
    """Foreign-key relationship used by the schema browser ER view."""

    from_table: str
    from_column: str
    to_table: str
    to_column: str
    constraint_name: str


@dataclass(slots=True)
class InsertableColumn:
    """Column metadata required to build a safe insert form."""

    name: str
    data_type: str
    is_nullable: bool
    has_default: bool
    is_primary_key: bool
    is_foreign_key: bool


@dataclass(slots=True)
class GeneratedQuery:
    """Response payload returned by the baseline query generator."""

    sql: str
    explanation: str
    results: list[dict[str, object]]
    tables_used: list[str]
    execution_time_ms: int


def _normalize_table_order(table_names: list[str]) -> list[str]:
    preferred = [
        "department",
        "person",
        "student",
        "faculty",
        "staff",
        "semester",
        "course",
        "course_prerequisite",
        "section",
        "enrollment",
        "assessment",
        "exam",
        "exam_result",
        "assignment",
        "assignment_submission",
        "fee_invoice",
        "fee_payment",
        "hostel",
        "hostel_room",
        "hostel_allotment",
    ]
    preferred_present = [table_name for table_name in preferred if table_name in table_names]
    remaining = sorted(table_name for table_name in table_names if table_name not in preferred_present)
    return preferred_present + remaining


def _classify_table(table_name: str) -> tuple[str, str]:
    if table_name in {"department", "person", "semester", "hostel"}:
        return "academic", "master"
    if table_name in {"student", "faculty", "staff", "course", "section"}:
        return "academic", "entity"
    if table_name in {"enrollment", "fee_invoice", "fee_payment", "hostel_allotment"}:
        return "finance" if "fee_" in table_name else "housing" if "hostel" in table_name else "academic", "transaction"
    if table_name in {"course_prerequisite", "exam_result", "assignment_submission", "hostel_room"}:
        return "academic" if table_name != "hostel_room" else "housing", "weak"
    if table_name in {"assessment", "exam", "assignment"}:
        return "academic", "weak"
    if table_name.startswith("hostel"):
        return "housing", "entity"
    if table_name.startswith("fee_"):
        return "finance", "transaction"
    return "academic", "entity"


def _quote_identifier(identifier: str) -> str:
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", identifier):
        raise ValueError("Invalid identifier.")
    return f'"{identifier}"'


def _validate_public_table_name(table_name: str) -> str:
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", table_name):
        raise ValueError("Invalid table name.")
    if table_name in EXCLUDED_SCHEMA_TABLES:
        raise ValueError("This table is not available.")
    return table_name


def _fetch_schema_rows() -> tuple[list[tuple[Any, ...]], list[tuple[Any, ...]], list[tuple[str, str]]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                c.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                c.is_identity
            FROM information_schema.columns AS c
            JOIN information_schema.tables AS t
              ON t.table_schema = c.table_schema
             AND t.table_name = c.table_name
            WHERE c.table_schema = 'public'
              AND t.table_type = 'BASE TABLE'
            ORDER BY c.table_name, c.ordinal_position;
            """
        )
        column_rows = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                tc.table_name,
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            LEFT JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            LEFT JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
             AND ccu.table_schema = tc.table_schema
            WHERE tc.table_schema = 'public'
            ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name, kcu.ordinal_position;
            """
        )
        constraint_rows = cursor.fetchall()

        cursor.execute(
            """
            SELECT table_name, view_definition
            FROM information_schema.views
            WHERE table_schema = 'public'
              AND table_name IN ('student_transcript', 'faculty_load', 'department_summary')
            ORDER BY table_name;
            """
        )
        view_rows = cursor.fetchall()

    return column_rows, constraint_rows, view_rows


def _build_schema_payload() -> dict[str, Any]:
    column_rows, constraint_rows, view_rows = _fetch_schema_rows()

    primary_key_columns: set[tuple[str, str]] = set()
    foreign_key_columns: set[tuple[str, str]] = set()
    relationships: list[SchemaRelationship] = []
    table_constraints: dict[str, dict[str, list[str]]] = {}

    for table_name, constraint_name, constraint_type, column_name, foreign_table_name, foreign_column_name in constraint_rows:
        if table_name in EXCLUDED_SCHEMA_TABLES:
            continue
        if constraint_type == "PRIMARY KEY" and column_name:
            primary_key_columns.add((table_name, column_name))
        if constraint_type == "FOREIGN KEY" and column_name and foreign_table_name and foreign_column_name:
            foreign_key_columns.add((table_name, column_name))
            if foreign_table_name not in EXCLUDED_SCHEMA_TABLES:
                relationships.append(
                    SchemaRelationship(
                        from_table=table_name,
                        from_column=column_name,
                        to_table=foreign_table_name,
                        to_column=foreign_column_name,
                        constraint_name=constraint_name,
                    )
                )
        if column_name:
            detail = ""
            if constraint_type == "PRIMARY KEY":
                detail = "pk"
            elif constraint_type == "UNIQUE":
                detail = "unique"
            elif constraint_type == "FOREIGN KEY" and foreign_table_name and foreign_column_name:
                detail = f"fk -> {foreign_table_name}.{foreign_column_name}"
            elif constraint_type == "CHECK":
                detail = "check"
            if detail:
                table_constraints.setdefault(table_name, {}).setdefault(column_name, []).append(detail)

    tables_by_name: dict[str, dict[str, Any]] = {}
    insertable_by_table: dict[str, list[InsertableColumn]] = {}

    for table_name, column_name, data_type, is_nullable, column_default, is_identity in column_rows:
        if table_name in EXCLUDED_SCHEMA_TABLES:
            continue

        column_constraints = table_constraints.get(table_name, {}).get(column_name, [])
        if (table_name, column_name) in primary_key_columns and "pk" not in column_constraints:
            column_constraints = ["pk", *column_constraints]

        if table_name not in tables_by_name:
            domain, entity_kind = _classify_table(table_name)
            tables_by_name[table_name] = {
                "name": table_name,
                "columns": [],
                "domain": domain,
                "entity_kind": entity_kind,
                "graph_modes": sorted([mode for mode, tables in GRAPH_MODE_TABLES.items() if table_name in tables] + ["all"]),
            }

        tables_by_name[table_name]["columns"].append(
            {
                "name": column_name,
                "type": data_type,
                "constraints": column_constraints,
            }
        )

        has_default = column_default is not None or is_identity == "YES"
        insertable_by_table.setdefault(table_name, []).append(
            InsertableColumn(
                name=column_name,
                data_type=data_type,
                is_nullable=is_nullable == "YES",
                has_default=has_default,
                is_primary_key=(table_name, column_name) in primary_key_columns,
                is_foreign_key=(table_name, column_name) in foreign_key_columns,
            )
        )

    table_names = _normalize_table_order(list(tables_by_name))
    tables = [tables_by_name[table_name] for table_name in table_names]
    insertable_tables = [
        {
            "name": table_name,
            "columns": [
                {
                    "name": column.name,
                    "type": column.data_type,
                    "required": not column.is_nullable and not column.has_default,
                    "foreign_key": column.is_foreign_key,
                    "primary_key": column.is_primary_key,
                }
                for column in insertable_by_table[table_name]
                if not column.is_primary_key or not column.has_default
            ],
        }
        for table_name in table_names
        if table_name not in EXCLUDED_INSERT_TABLES
    ]

    return {
        "tables": tables,
        "views": [view_name for view_name, _definition in view_rows],
        "relationships": [
            {
                "from_table": rel.from_table,
                "from_column": rel.from_column,
                "to_table": rel.to_table,
                "to_column": rel.to_column,
                "constraint_name": rel.constraint_name,
            }
            for rel in relationships
            if rel.from_table in table_names and rel.to_table in table_names
        ],
        "insertable_tables": insertable_tables,
    }


def execute_demo_sql(sql: str, params: list[object] | None = None) -> list[dict[str, object]]:
    """Execute a deterministic read-only demo SQL template."""
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def get_schema_payload() -> dict[str, object]:
    """Return a compact schema payload for the frontend."""
    try:
        payload = _build_schema_payload()
    except DatabaseError:
        payload = {
            "tables": [],
            "views": [],
            "relationships": [],
            "insertable_tables": [],
        }
    payload["serialized"] = serialize_schema(include_views=True)
    return payload


def get_insertable_table_metadata(table_name: str) -> list[InsertableColumn]:
    """Return insertable column metadata for a whitelisted public table."""
    table_name = _validate_public_table_name(table_name)
    if table_name in EXCLUDED_INSERT_TABLES:
        raise ValueError("This table is not available for inserts.")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                c.is_identity,
                EXISTS (
                    SELECT 1
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.table_schema = kcu.table_schema
                    WHERE tc.table_schema = 'public'
                      AND tc.table_name = c.table_name
                      AND tc.constraint_type = 'PRIMARY KEY'
                      AND kcu.column_name = c.column_name
                ) AS is_primary_key,
                EXISTS (
                    SELECT 1
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.table_schema = kcu.table_schema
                    WHERE tc.table_schema = 'public'
                      AND tc.table_name = c.table_name
                      AND tc.constraint_type = 'FOREIGN KEY'
                      AND kcu.column_name = c.column_name
                ) AS is_foreign_key
            FROM information_schema.columns AS c
            JOIN information_schema.tables AS t
              ON t.table_schema = c.table_schema
             AND t.table_name = c.table_name
            WHERE c.table_schema = 'public'
              AND t.table_type = 'BASE TABLE'
              AND c.table_name = %s
            ORDER BY c.ordinal_position;
            """,
            [table_name],
        )
        rows = cursor.fetchall()

    if not rows:
        raise ValueError("Unknown table.")

    return [
        InsertableColumn(
            name=column_name,
            data_type=data_type,
            is_nullable=is_nullable == "YES",
            has_default=column_default is not None or is_identity == "YES",
            is_primary_key=bool(is_primary_key),
            is_foreign_key=bool(is_foreign_key),
        )
        for column_name, data_type, is_nullable, column_default, is_identity, is_primary_key, is_foreign_key in rows
    ]


def insert_record(table_name: str, record: dict[str, Any]) -> dict[str, Any]:
    """Safely insert a single record into a whitelisted table and return the inserted row."""
    metadata = get_insertable_table_metadata(table_name)
    insertable_columns = {
        column.name: column
        for column in metadata
        if not column.is_primary_key or not column.has_default
    }
    required_columns = {
        column.name
        for column in metadata
        if not column.is_primary_key and not column.has_default and not column.is_nullable
    }

    unknown_columns = sorted(set(record) - set(insertable_columns))
    if unknown_columns:
        raise ValueError(f"Unknown or non-insertable columns: {', '.join(unknown_columns)}")

    missing_columns = sorted(column for column in required_columns if column not in record)
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    if not record:
        raise ValueError("Record payload cannot be empty.")

    column_names = list(record)
    placeholders = ", ".join(["%s"] * len(column_names))
    quoted_columns = ", ".join(f'"{column_name}"' for column_name in column_names)
    sql = f'INSERT INTO "{table_name}" ({quoted_columns}) VALUES ({placeholders}) RETURNING *;'

    with connection.cursor() as cursor:
        cursor.execute(sql, [record[column_name] for column_name in column_names])
        inserted_row = cursor.fetchone()
        column_labels = [column[0] for column in cursor.description]
    return dict(zip(column_labels, inserted_row, strict=True))


def _table_common_queries(table_name: str) -> list[str]:
    suggestions = {
        "student": [
            "Show top 10 students by GPA",
            "List students admitted after 2024",
            "Find students with attendance below 75 percent",
        ],
        "faculty": [
            "Show faculty teaching load this semester",
            "List faculty members by designation",
            "Find faculty with no assigned sections",
        ],
        "course": [
            "Show all core courses with four credits",
            "Find courses with prerequisites",
            "Show average grade points by course",
        ],
        "enrollment": [
            "Show enrollment count by course and semester",
            "Find sections with fewer than 10 enrollments",
            "Show students enrolled in Database Systems",
        ],
        "fee_invoice": [
            "List unpaid fee invoices",
            "Show total fees paid by semester",
            "Show outstanding balance by student",
        ],
        "hostel_allotment": [
            "List active hostel allotments",
            "Show hostel occupancy by floor",
            "Find hostel allotments ending this semester",
        ],
    }
    return suggestions.get(table_name, [f"Show me all records from {table_name}"])


def get_table_intelligence(table_name: str) -> dict[str, Any]:
    """Return stats, examples, and metadata for a table intelligence panel."""
    table_name = _validate_public_table_name(table_name)
    metadata = get_insertable_table_metadata(table_name)
    pk_columns = [column.name for column in metadata if column.is_primary_key]
    fk_columns = [column.name for column in metadata if column.is_foreign_key]
    pk_order = ", ".join(_quote_identifier(column) for column in pk_columns) if pk_columns else ""
    order_clause = f" ORDER BY {pk_order} DESC" if pk_order else ""
    quoted_table = _quote_identifier(table_name)

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {quoted_table};")
        row_count = int(cursor.fetchone()[0])

        cursor.execute(
            """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = %s
            ORDER BY indexname;
            """,
            [table_name],
        )
        indexes = [{"name": name, "definition": definition} for name, definition in cursor.fetchall()]

        cursor.execute(
            f"SELECT * FROM {quoted_table}{order_clause} LIMIT 3;"
        )
        sample_columns = [column[0] for column in cursor.description]
        recent_rows = [dict(zip(sample_columns, row, strict=True)) for row in cursor.fetchall()]

        cursor.execute(
            f"SELECT * FROM {quoted_table} LIMIT 3;"
        )
        preview_columns = [column[0] for column in cursor.description]
        sample_rows = [dict(zip(preview_columns, row, strict=True)) for row in cursor.fetchall()]

        null_rate_parts = [
            f"ROUND(AVG(CASE WHEN {_quote_identifier(column.name)} IS NULL THEN 1.0 ELSE 0.0 END) * 100, 2) AS {_quote_identifier(column.name)}"
            for column in metadata[: min(8, len(metadata))]
        ]
        null_rates: dict[str, float] = {}
        if null_rate_parts:
            cursor.execute(f"SELECT {', '.join(null_rate_parts)} FROM {quoted_table};")
            null_rate_row = cursor.fetchone()
            null_rates = {
                metadata[index].name: float(value or 0)
                for index, value in enumerate(null_rate_row)
            }

    domain, entity_kind = _classify_table(table_name)
    return {
        "table_name": table_name,
        "row_count": row_count,
        "primary_keys": pk_columns,
        "foreign_keys": fk_columns,
        "null_rates": null_rates,
        "index_count": len(indexes),
        "indexes": indexes[:6],
        "sample_rows": sample_rows,
        "recent_rows": recent_rows,
        "common_queries": _table_common_queries(table_name),
        "domain": domain,
        "entity_kind": entity_kind,
    }


def get_relationship_preview(from_table: str, from_column: str, to_table: str, to_column: str) -> dict[str, Any]:
    """Return sample joined rows for a foreign-key relationship."""
    from_table = _validate_public_table_name(from_table)
    to_table = _validate_public_table_name(to_table)
    from_column = re.sub(r"[^a-z0-9_]", "", from_column.lower())
    to_column = re.sub(r"[^a-z0-9_]", "", to_column.lower())
    if not from_column or not to_column:
        raise ValueError("Invalid relationship columns.")

    quoted_from_table = _quote_identifier(from_table)
    quoted_to_table = _quote_identifier(to_table)
    quoted_from_column = _quote_identifier(from_column)
    quoted_to_column = _quote_identifier(to_column)
    sql = (
        f"SELECT row_to_json(src) AS source_row, row_to_json(dst) AS target_row "
        f"FROM {quoted_from_table} AS src "
        f"JOIN {quoted_to_table} AS dst "
        f"ON src.{quoted_from_column} = dst.{quoted_to_column} "
        "LIMIT 5;"
    )
    with connection.cursor() as cursor:
        cursor.execute(sql)
        rows = [
            {
                "source_row": source_row,
                "target_row": target_row,
            }
            for source_row, target_row in cursor.fetchall()
        ]
    return {
        "sql": sql,
        "row_count": len(rows),
        "rows": rows,
        "relationship": {
            "from_table": from_table,
            "from_column": from_column,
            "to_table": to_table,
            "to_column": to_column,
        },
    }


def extract_limit(natural_language: str, default: int = 25, maximum: int = 100) -> int:
    """Infer a row limit from the prompt while keeping the API bounded."""
    normalized = natural_language.lower()
    digit_match = re.search(r"\b(?:top|limit|show|list|find)\s+(\d{1,3})\b", normalized)
    if digit_match:
        return min(max(1, int(digit_match.group(1))), maximum)

    word_to_number = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "fifteen": 15,
        "twenty": 20,
        "twenty five": 25,
        "fifty": 50,
        "hundred": 100,
    }
    for phrase, value in sorted(word_to_number.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"\b(?:top|limit|show|list|find)\s+{re.escape(phrase)}\b", normalized):
            return min(value, maximum)
    return default


def generate_demo_query(natural_language: str) -> GeneratedQuery:
    """Generate and execute a safe deterministic SQL response for local demos."""
    start = perf_counter()
    normalized = natural_language.lower()
    limit = extract_limit(natural_language)

    city_match = re.search(r"\b(?:from|in|city|belong(?:s)? to)\s+([a-z][a-z\s-]{1,60})", normalized)
    city_name = ""
    if city_match and "attendance" not in normalized:
        city_name = city_match.group(1)
        city_name = re.split(r"\b(?:with|and|where|order|limit|having|above|below|greater|less)\b", city_name, maxsplit=1)[0]
        city_name = city_name.strip(" .?!")

    if city_name and "student" in normalized:
        safe_city_name = city_name.replace("'", "''")
        sql = (
            "SELECT s.roll_number, p.first_name || ' ' || p.last_name AS student_name, "
            "p.city, p.state, d.department_name, s.program_level, s.current_year, s.cgpa, s.status "
            "FROM student AS s "
            "JOIN person AS p ON p.person_id = s.student_id "
            "JOIN department AS d ON d.department_id = s.department_id "
            f"WHERE p.city ILIKE '{safe_city_name}' "
            "ORDER BY student_name ASC "
            f"LIMIT {limit};"
        )
        tables_used = ["student", "person", "department"]
        explanation = f"Lists students whose city is {city_name.title()}, including city and state in the output."
    elif "attendance" in normalized and ("below" in normalized or "less" in normalized or "under" in normalized or "low" in normalized):
        threshold_match = re.search(r"\b(?:below|less than|under)\s+(\d{1,3})(?:\s*percent|%)?\b", normalized)
        threshold = min(max(0, int(threshold_match.group(1))) if threshold_match else 75, 100)
        sql = (
            "SELECT s.roll_number, p.first_name || ' ' || p.last_name AS student_name, "
            "p.city, p.state, d.department_name, c.course_code, c.course_title, "
            "e.attendance_pct, e.enrollment_status, e.final_grade_letter "
            "FROM enrollment AS e "
            "JOIN student AS s ON s.student_id = e.student_id "
            "JOIN person AS p ON p.person_id = s.student_id "
            "JOIN section AS sec ON sec.section_id = e.section_id "
            "JOIN course AS c ON c.course_id = sec.course_id "
            "JOIN department AS d ON d.department_id = s.department_id "
            f"WHERE e.attendance_pct < {threshold} "
            "ORDER BY e.attendance_pct ASC, student_name ASC "
            f"LIMIT {limit};"
        )
        tables_used = ["enrollment", "student", "person", "section", "course", "department"]
        explanation = f"Finds student enrollment records with attendance below {threshold} percent and includes student, city, department, and course context."
    elif "unpaid" in normalized or "overdue" in normalized or "outstanding" in normalized:
        sql = (
            "SELECT s.roll_number, d.department_name, fi.invoice_number, fi.total_amount, fi.status, fi.due_date "
            "FROM fee_invoice AS fi "
            "JOIN student AS s ON s.student_id = fi.student_id "
            "JOIN department AS d ON d.department_id = s.department_id "
            "WHERE fi.status IN ('unpaid', 'overdue', 'partial') "
            "ORDER BY fi.due_date ASC, fi.total_amount DESC "
            f"LIMIT {limit};"
        )
        tables_used = ["fee_invoice", "student", "department"]
        explanation = "Finds unpaid, overdue, and partially paid invoices with student and department context."
    elif "fee" in normalized or "payment" in normalized or "revenue" in normalized or "scholarship" in normalized:
        sql = (
            "SELECT sem.academic_year, sem.term_name, "
            "ROUND(SUM(fi.total_amount), 2) AS invoiced_amount, "
            "ROUND(COALESCE(SUM(fp.amount_paid), 0), 2) AS paid_amount, "
            "COUNT(DISTINCT fi.invoice_id) AS invoice_count "
            "FROM fee_invoice AS fi "
            "JOIN semester AS sem ON sem.semester_id = fi.semester_id "
            "LEFT JOIN fee_payment AS fp ON fp.invoice_id = fi.invoice_id AND fp.payment_status = 'success' "
            "GROUP BY sem.academic_year, sem.term_name "
            "ORDER BY paid_amount DESC "
            f"LIMIT {limit};"
        )
        tables_used = ["fee_invoice", "fee_payment", "semester"]
        explanation = "Aggregates invoiced and paid fee amounts by semester."
    elif "hostel" in normalized or "room" in normalized or "occupancy" in normalized:
        sql = (
            "SELECT h.hostel_name, h.hostel_type, h.capacity, COUNT(ha.allotment_id) AS active_allotments, "
            "ROUND((COUNT(ha.allotment_id)::NUMERIC / NULLIF(h.capacity, 0)) * 100, 2) AS occupancy_pct "
            "FROM hostel AS h "
            "LEFT JOIN hostel_room AS hr ON hr.hostel_id = h.hostel_id "
            "LEFT JOIN hostel_allotment AS ha ON ha.room_id = hr.room_id AND ha.status = 'active' "
            "GROUP BY h.hostel_id, h.hostel_name, h.hostel_type, h.capacity "
            "ORDER BY occupancy_pct DESC NULLS LAST, active_allotments DESC "
            f"LIMIT {limit};"
        )
        tables_used = ["hostel", "hostel_room", "hostel_allotment"]
        explanation = "Shows hostel capacity and active allotment-based occupancy."
    elif "faculty" in normalized or "professor" in normalized or "teaching" in normalized or "workload" in normalized:
        sql = (
            "SELECT f.employee_code, p.first_name || ' ' || p.last_name AS faculty_name, "
            "d.department_name, f.designation, COUNT(sec.section_id) AS sections_taught "
            "FROM faculty AS f "
            "JOIN person AS p ON p.person_id = f.faculty_id "
            "JOIN department AS d ON d.department_id = f.department_id "
            "LEFT JOIN section AS sec ON sec.faculty_id = f.faculty_id "
            "GROUP BY f.faculty_id, f.employee_code, p.first_name, p.last_name, d.department_name, f.designation "
            "ORDER BY sections_taught DESC, faculty_name ASC "
            f"LIMIT {limit};"
        )
        tables_used = ["faculty", "person", "department", "section"]
        explanation = "Calculates faculty teaching load by counting assigned sections."
    elif "course" in normalized or "prerequisite" in normalized:
        course_filters: list[str] = []
        if "core" in normalized:
            course_filters.append("c.course_type = 'core'")
        elif "elective" in normalized:
            course_filters.append("c.course_type = 'elective'")
        elif "lab" in normalized:
            course_filters.append("c.course_type = 'lab'")
        elif "seminar" in normalized:
            course_filters.append("c.course_type = 'seminar'")
        if "four" in normalized or "4 credit" in normalized or "4-credit" in normalized:
            course_filters.append("c.credits = 4")
        elif "three" in normalized or "3 credit" in normalized or "3-credit" in normalized:
            course_filters.append("c.credits = 3")
        where_clause = f"WHERE {' AND '.join(course_filters)} " if course_filters else ""
        sql = (
            "SELECT c.course_code, c.course_title, d.department_name, c.credits, c.course_type, "
            "COUNT(cp.prerequisite_course_id) AS prerequisite_count "
            "FROM course AS c "
            "JOIN department AS d ON d.department_id = c.department_id "
            "LEFT JOIN course_prerequisite AS cp ON cp.course_id = c.course_id "
            f"{where_clause}"
            "GROUP BY c.course_id, c.course_code, c.course_title, d.department_name, c.credits, c.course_type "
            "ORDER BY prerequisite_count DESC, c.course_code ASC "
            f"LIMIT {limit};"
        )
        tables_used = ["course", "department", "course_prerequisite"]
        explanation = "Lists courses with department, credit, type, and prerequisite counts."
    elif "exam" in normalized or "assignment" in normalized or "assessment" in normalized or "marks" in normalized:
        sql = (
            "SELECT c.course_code, a.title, a.assessment_type, "
            "ROUND(AVG(er.marks_obtained), 2) AS avg_exam_marks, COUNT(er.student_id) AS evaluated_students "
            "FROM assessment AS a "
            "JOIN section AS sec ON sec.section_id = a.section_id "
            "JOIN course AS c ON c.course_id = sec.course_id "
            "LEFT JOIN exam AS ex ON ex.exam_id = a.assessment_id "
            "LEFT JOIN exam_result AS er ON er.exam_id = ex.exam_id "
            "GROUP BY c.course_code, a.title, a.assessment_type "
            "ORDER BY evaluated_students DESC, avg_exam_marks DESC NULLS LAST "
            f"LIMIT {limit};"
        )
        tables_used = ["assessment", "exam", "exam_result", "section", "course"]
        explanation = "Summarizes assessment and exam performance by course."
    elif "grade" in normalized or "gpa" in normalized or "cgpa" in normalized or "rank" in normalized or "top" in normalized:
        sql = (
            "SELECT s.roll_number, p.first_name || ' ' || p.last_name AS student_name, "
            "d.department_name, s.cgpa, "
            "RANK() OVER (PARTITION BY d.department_id ORDER BY s.cgpa DESC NULLS LAST) AS department_rank "
            "FROM student AS s "
            "JOIN person AS p ON p.person_id = s.student_id "
            "JOIN department AS d ON d.department_id = s.department_id "
            "ORDER BY s.cgpa DESC NULLS LAST, s.roll_number ASC "
            f"LIMIT {limit};"
        )
        tables_used = ["student", "person", "department"]
        explanation = "Ranks students by CGPA while showing department context."
    elif "enrollment" in normalized or "attendance" in normalized or "section" in normalized:
        sql = (
            "SELECT d.department_name, c.course_code, sem.academic_year, sem.term_name, "
            "COUNT(e.enrollment_id) AS enrollments, ROUND(AVG(e.attendance_pct), 2) AS avg_attendance "
            "FROM enrollment AS e "
            "JOIN section AS sec ON sec.section_id = e.section_id "
            "JOIN course AS c ON c.course_id = sec.course_id "
            "JOIN department AS d ON d.department_id = c.department_id "
            "JOIN semester AS sem ON sem.semester_id = sec.semester_id "
            "GROUP BY d.department_name, c.course_code, sem.academic_year, sem.term_name "
            "ORDER BY enrollments DESC, avg_attendance DESC NULLS LAST "
            f"LIMIT {limit};"
        )
        tables_used = ["enrollment", "section", "course", "department", "semester"]
        explanation = "Aggregates enrollment and attendance by course and semester."
    elif "history" in normalized or "query" in normalized:
        sql = (
            "SELECT user_input, execution_status, execution_time_ms, result_row_count, created_at "
            "FROM query_log "
            "ORDER BY created_at DESC "
            f"LIMIT {limit};"
        )
        tables_used = ["query_log"]
        explanation = "Returns recent query history for learning and debugging."
    elif "department" in normalized or "summary" in normalized or "count" in normalized:
        sql = (
            "SELECT d.department_name, COUNT(DISTINCT s.student_id) AS student_count, "
            "COUNT(DISTINCT f.faculty_id) AS faculty_count, COUNT(DISTINCT c.course_id) AS course_count "
            "FROM department AS d "
            "LEFT JOIN student AS s ON s.department_id = d.department_id "
            "LEFT JOIN faculty AS f ON f.department_id = d.department_id "
            "LEFT JOIN course AS c ON c.department_id = d.department_id "
            "GROUP BY d.department_id, d.department_name "
            "ORDER BY student_count DESC, faculty_count DESC "
            f"LIMIT {limit};"
        )
        tables_used = ["department", "student", "faculty", "course"]
        explanation = "Summarizes department size across students, faculty, and courses."
    else:
        sql = (
            "SELECT s.roll_number, p.first_name || ' ' || p.last_name AS student_name, d.department_name, s.cgpa "
            "FROM student AS s "
            "JOIN person AS p ON p.person_id = s.student_id "
            "JOIN department AS d ON d.department_id = s.department_id "
            "ORDER BY s.cgpa DESC NULLS LAST "
            f"LIMIT {limit};"
        )
        tables_used = ["student", "person", "department"]
        explanation = "Returns a default leaderboard of top students by CGPA."

    results = execute_demo_sql(sql)
    return GeneratedQuery(
        sql=sql,
        explanation=explanation,
        results=results,
        tables_used=tables_used,
        execution_time_ms=max(40, int((perf_counter() - start) * 1000)),
    )


def run_querymind_query(natural_language: str, prior_sql: str | None = None) -> dict[str, object]:
    """Execute the primary NL2SQL path with a deterministic local fallback."""
    start = perf_counter()
    effective_prompt = natural_language
    if prior_sql:
        effective_prompt = (
            f"Previous SQL the user just ran:\n{prior_sql}\n\n"
            f"Follow-up question (refine the previous query):\n{natural_language}"
        )
    try:
        payload = NL2SQLAgent().run_with_retries(effective_prompt)
        return {
            "sql": payload["sql"],
            "results": payload["results"],
            "explanation": payload["explanation"],
            "execution_time": max(40, int((perf_counter() - start) * 1000)),
            "tables_used": payload.get("tables_used", []),
            "complexity_level": payload.get("complexity_level", "llm"),
            "confidence": payload.get("confidence", 0.92),
            "reasoning": payload.get("reasoning", ""),
        }
    except Exception:
        fallback = generate_demo_query(natural_language)
        return {
            "sql": fallback.sql,
            "results": fallback.results,
            "explanation": fallback.explanation,
            "execution_time": fallback.execution_time_ms,
            "tables_used": fallback.tables_used,
            "complexity_level": "fallback",
            "confidence": 0.78,
            "reasoning": "Local deterministic router selected this template based on keywords in the prompt.",
        }


def _safe_select_sql(raw_sql: str) -> str:
    """Validate that the supplied SQL is a single read-only SELECT/CTE statement."""
    if not raw_sql or not raw_sql.strip():
        raise ValueError("SQL is required.")
    sql = raw_sql.strip().rstrip(";")
    if ";" in sql:
        raise ValueError("Only a single statement is allowed.")
    try:
        NL2SQLAgent().validate(sql)
    except UnsafeQueryError as exc:
        raise ValueError(str(exc)) from exc
    return sql


def explain_sql(raw_sql: str) -> dict[str, Any]:
    """Run EXPLAIN (FORMAT JSON) for a validated read-only SQL statement."""
    sql = _safe_select_sql(raw_sql)
    explain_query = f"EXPLAIN (FORMAT JSON, VERBOSE FALSE, COSTS TRUE) {sql}"
    with connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION READ ONLY;")
        cursor.execute(explain_query)
        rows = cursor.fetchall()
    if not rows:
        return {"plan": None, "summary": "Plan unavailable."}
    raw_plan = rows[0][0]
    if isinstance(raw_plan, str):
        raw_plan = json.loads(raw_plan)
    plan_root = raw_plan[0]["Plan"] if isinstance(raw_plan, list) else raw_plan.get("Plan")
    return {
        "plan": plan_root,
        "raw": raw_plan,
        "summary": _summarize_plan(plan_root),
    }


def _summarize_plan(plan: dict[str, Any] | None) -> str:
    """Produce a one-line description of the top-level plan node."""
    if not plan:
        return "No plan available."
    node_type = plan.get("Node Type", "Unknown")
    cost = plan.get("Total Cost", 0)
    rows = plan.get("Plan Rows", 0)
    return f"{node_type} · cost {cost:.2f} · ~{rows} rows"


def repair_sql(failing_sql: str, error_message: str, natural_language: str = "") -> dict[str, Any]:
    """Attempt to repair failing SQL using Claude when available, otherwise heuristic fixes."""
    sql = (failing_sql or "").strip()
    if not sql:
        raise ValueError("Original SQL is required.")
    error_message = (error_message or "").strip() or "unknown error"

    agent = NL2SQLAgent()
    if agent.client is not None:
        repair_prompt = (
            "The following PostgreSQL query failed. Repair it while preserving the user's intent. "
            "Return strict JSON with keys: sql, explanation, fix_summary, tables_used.\n\n"
            f"User intent: {natural_language or 'not provided'}\n\n"
            f"Failing SQL:\n{sql}\n\n"
            f"Database error:\n{error_message}\n"
        )
        try:
            payload = agent.generate(repair_prompt)
            repaired_sql = _safe_select_sql(str(payload.get("sql", sql)))
            results, _ = agent.execute(repaired_sql)
            return {
                "original_sql": sql,
                "repaired_sql": repaired_sql,
                "results": results,
                "fix_summary": payload.get("fix_summary") or payload.get("explanation", "Repaired by Claude."),
                "explanation": payload.get("explanation", "Claude rewrote the query to satisfy schema constraints."),
                "tables_used": payload.get("tables_used", []),
                "source": "claude",
            }
        except Exception:
            pass

    # Heuristic fallback: best-effort cleanup of common issues.
    repaired_sql = re.sub(r"\bGROUP\s+BY\s+1\s*,\s*2\b", "GROUP BY 1", sql, flags=re.IGNORECASE)
    repaired_sql = repaired_sql.replace("LIMIT 0", "LIMIT 25")
    if "limit" not in repaired_sql.lower():
        repaired_sql = repaired_sql.rstrip(";") + " LIMIT 25"
    repaired_sql = _safe_select_sql(repaired_sql)
    try:
        results, _ = agent.execute(repaired_sql)
    except Exception as exc:  # pragma: no cover
        raise ValueError(f"Auto-repair failed: {exc}") from exc
    return {
        "original_sql": sql,
        "repaired_sql": repaired_sql,
        "results": results,
        "fix_summary": "Applied heuristic limit and grouping cleanup.",
        "explanation": "Local heuristic repair clamped row limits and trimmed grouping noise.",
        "tables_used": [],
        "source": "heuristic",
    }


def compute_metrics() -> dict[str, Any]:
    """Aggregate live query log statistics for the metrics strip."""
    from .models import QueryLog  # local import to avoid app-loading order issues

    aggregates: dict[str, Any] = {
        "total_queries": 0,
        "successful_queries": 0,
        "failed_queries": 0,
        "today_queries": 0,
        "avg_latency_ms": 0,
        "p95_latency_ms": 0,
        "fastest_ms": 0,
        "slowest_ms": 0,
        "rows_returned": 0,
        "unique_tables": 0,
    }
    try:
        all_logs = list(QueryLog.objects.all().values(
            "execution_status",
            "execution_time_ms",
            "result_row_count",
            "created_at",
            "generated_sql",
        ))
    except DatabaseError:
        return aggregates

    total = len(all_logs)
    if total == 0:
        return aggregates

    success = sum(1 for log in all_logs if log["execution_status"] == "success")
    latencies = sorted(int(log["execution_time_ms"] or 0) for log in all_logs)
    p95_index = max(0, int(round(0.95 * (len(latencies) - 1))))
    rows_total = sum(int(log["result_row_count"] or 0) for log in all_logs)

    from datetime import timezone

    today = max(log["created_at"] for log in all_logs).astimezone(timezone.utc).date()
    today_count = sum(1 for log in all_logs if log["created_at"].astimezone(timezone.utc).date() == today)

    table_pattern = re.compile(r"\bfrom\s+([a-z_][a-z0-9_]*)|\bjoin\s+([a-z_][a-z0-9_]*)", re.IGNORECASE)
    unique_tables: set[str] = set()
    for log in all_logs:
        for match in table_pattern.findall(log["generated_sql"] or ""):
            for token in match:
                if token:
                    unique_tables.add(token.lower())

    aggregates.update(
        {
            "total_queries": total,
            "successful_queries": success,
            "failed_queries": total - success,
            "today_queries": today_count,
            "avg_latency_ms": int(sum(latencies) / len(latencies)) if latencies else 0,
            "p95_latency_ms": latencies[p95_index] if latencies else 0,
            "fastest_ms": latencies[0] if latencies else 0,
            "slowest_ms": latencies[-1] if latencies else 0,
            "rows_returned": rows_total,
            "unique_tables": len(unique_tables),
            "success_rate": round((success / total) * 100, 1) if total else 0,
        }
    )
    return aggregates


def get_query_log_detail(query_log_id: int) -> dict[str, Any]:
    """Return a single QueryLog record for share-link hydration."""
    from .models import QueryLog

    try:
        log = QueryLog.objects.get(pk=query_log_id)
    except QueryLog.DoesNotExist as exc:
        raise ValueError("Saved query not found.") from exc

    return {
        "id": log.id,
        "user_input": log.user_input,
        "generated_sql": log.generated_sql,
        "explanation": log.explanation,
        "execution_status": log.execution_status,
        "execution_time_ms": log.execution_time_ms,
        "result_row_count": log.result_row_count,
        "created_at": log.created_at.isoformat(),
    }


def stream_query_tokens(natural_language: str):
    """Generate SSE-friendly token chunks for the live SQL typewriter overlay."""
    text = natural_language.strip() or "Show top 10 students by GPA"
    yield {"stage": "reading_schema", "token": "Reading schema and indexes"}

    try:
        result = run_querymind_query(text)
    except Exception as exc:  # pragma: no cover
        yield {"stage": "error", "token": f"error: {exc}"}
        return

    sql = str(result.get("sql", ""))
    yield {"stage": "generating_sql", "token": "Generating SQL"}

    chunk_size = max(4, len(sql) // 28)
    for index in range(0, len(sql), chunk_size):
        yield {
            "stage": "generating_sql",
            "token": sql[index : index + chunk_size],
            "kind": "sql_chunk",
        }

    yield {"stage": "executing_query", "token": "Executing against PostgreSQL"}
    yield {
        "stage": "complete",
        "token": "Done",
        "result": {
            "sql": sql,
            "results": result.get("results", []),
            "explanation": result.get("explanation", ""),
            "execution_time": result.get("execution_time", 0),
            "tables_used": result.get("tables_used", []),
            "complexity_level": result.get("complexity_level", "llm"),
            "confidence": result.get("confidence", 0.9),
            "reasoning": result.get("reasoning", ""),
        },
    }
