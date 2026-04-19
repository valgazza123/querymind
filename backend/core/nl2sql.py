"""Schema-aware NL2SQL utilities for QueryMind."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

import sqlparse
from django.db import connection
from django.db.utils import DatabaseError

try:
    from anthropic import Anthropic
except ImportError:  # pragma: no cover
    Anthropic = None  # type: ignore[assignment]


def serialize_schema(include_views: bool = True) -> str:
    """Serialize public schema tables, columns, constraints, and view definitions."""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    c.table_name,
                    c.column_name,
                    c.data_type,
                    c.is_nullable
                FROM information_schema.columns AS c
                WHERE c.table_schema = 'public'
                ORDER BY c.table_name, c.ordinal_position;
                """
            )
            column_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    tc.table_name,
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
                ORDER BY tc.table_name, tc.constraint_type, kcu.column_name;
                """
            )
            constraint_rows = cursor.fetchall()

            view_rows: list[tuple[str, str]] = []
            if include_views:
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
    except DatabaseError:
        return "Schema introspection unavailable until PostgreSQL migrations and SQL bootstrap complete."

    grouped: dict[str, list[str]] = {}
    for table_name, column_name, data_type, is_nullable in column_rows:
        grouped.setdefault(table_name, []).append(
            f"- {column_name}: {data_type}{' nullable' if is_nullable == 'YES' else ''}"
        )

    constraints: dict[str, list[str]] = {}
    for table_name, constraint_type, column_name, foreign_table_name, foreign_column_name in constraint_rows:
        detail = f"{constraint_type}({column_name})"
        if foreign_table_name and foreign_column_name:
            detail += f" -> {foreign_table_name}({foreign_column_name})"
        constraints.setdefault(table_name, []).append(detail)

    sections: list[str] = []
    for table_name in sorted(grouped):
        lines = [f"TABLE {table_name}"]
        lines.extend(grouped[table_name])
        if table_name in constraints:
            lines.append("constraints:")
            lines.extend(f"- {item}" for item in constraints[table_name])
        sections.append("\n".join(lines))

    if include_views and view_rows:
        sections.append("VIEWS")
        for view_name, definition in view_rows:
            sections.append(f"VIEW {view_name}\n{definition}")

    return "\n\n".join(sections)


@dataclass(slots=True)
class SimilarQuery:
    """Stored successful query used as a few-shot example."""

    user_input: str
    generated_sql: str
    explanation: str
    similarity: float


def find_similar_queries(user_input: str, limit: int = 5) -> list[SimilarQuery]:
    """Return the most similar successful query examples from query history."""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_input, generated_sql, COALESCE(explanation, '')
                FROM query_log
                WHERE execution_status = 'success'
                ORDER BY created_at DESC
                LIMIT 100;
                """
            )
            rows = cursor.fetchall()
    except DatabaseError:
        return []

    scored: list[SimilarQuery] = []
    for previous_input, generated_sql, explanation in rows:
        similarity = SequenceMatcher(None, user_input.lower(), previous_input.lower()).ratio()
        scored.append(
            SimilarQuery(
                user_input=previous_input,
                generated_sql=generated_sql,
                explanation=explanation,
                similarity=similarity,
            )
        )
    return sorted(scored, key=lambda item: item.similarity, reverse=True)[:limit]


class UnsafeQueryError(ValueError):
    """Raised when generated SQL violates safety rules."""


class NL2SQLAgent:
    """Generate, validate, and execute safe SQL queries using Claude."""

    def __init__(self, model: str = "claude-sonnet-4-20250514") -> None:
        """Initialize the agent with environment-based API configuration."""
        self.model = model
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if self.api_key and Anthropic is not None else None

    def _build_system_prompt(self, schema_text: str, examples: list[SimilarQuery]) -> str:
        """Construct the system prompt with schema context and safety rules."""
        example_block = "\n\n".join(
            [
                f"User: {item.user_input}\nSQL: {item.generated_sql}\nExplanation: {item.explanation}"
                for item in examples
            ]
        )
        return (
            "You are QueryMind, a PostgreSQL NL2SQL engine.\n"
            "Use the supplied schema exactly.\n"
            "Always prefer CTEs over deeply nested subqueries when readability improves.\n"
            "Always generate read-only SQL. Use parameter placeholders like %s when filtering dynamic user values.\n"
            "Prefer the views student_transcript, faculty_load, and department_summary when relevant.\n"
            "Refuse dangerous SQL such as DROP, TRUNCATE, ALTER, INSERT, UPDATE, DELETE without a restrictive WHERE clause.\n"
            "Return strict JSON with keys: sql, explanation, tables_used, complexity_level.\n\n"
            f"Schema:\n{schema_text}\n\n"
            f"Similar successful examples:\n{example_block}"
        )

    def generate(self, natural_language_query: str) -> dict[str, Any]:
        """Generate SQL JSON from a natural-language prompt."""
        schema_text = serialize_schema(include_views=True)
        examples = find_similar_queries(natural_language_query)

        if self.client is None:
            raise RuntimeError("Anthropic API key is unavailable; using local deterministic NL2SQL router.")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            system=self._build_system_prompt(schema_text, examples),
            messages=[{"role": "user", "content": natural_language_query}],
        )
        content = "".join(block.text for block in response.content if getattr(block, "text", None))
        return json.loads(content)

    def validate(self, sql: str) -> str:
        """Validate SQL structure and reject unsafe statements."""
        parsed = sqlparse.parse(sql)
        if not parsed:
            raise UnsafeQueryError("SQL could not be parsed.")

        normalized = sql.strip().lower()
        forbidden_keywords = ("drop ", "truncate ", "alter ", "grant ", "revoke ", "insert ", "update ", "delete ")
        if any(keyword in normalized for keyword in forbidden_keywords):
            raise UnsafeQueryError("Dangerous SQL statement detected.")
        if not normalized.startswith(("select", "with")):
            raise UnsafeQueryError("Only SELECT/CTE queries are allowed.")
        return sql

    def execute(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> tuple[list[dict[str, Any]], int]:
        """Execute validated SQL through the configured database connection."""
        validated_sql = self.validate(sql)
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY;")
            cursor.execute(validated_sql, params or [])
            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
        return rows, len(rows)

    def run_with_retries(self, natural_language_query: str, params: list[Any] | None = None, retries: int = 2) -> dict[str, Any]:
        """Generate SQL and retry with execution feedback up to the configured limit."""
        last_error = ""
        for attempt in range(retries + 1):
            payload = self.generate(natural_language_query if attempt == 0 else f"{natural_language_query}\nPrevious error: {last_error}")
            sql = self.validate(str(payload["sql"]))
            try:
                rows, row_count = self.execute(sql, params=params)
                payload["results"] = rows
                payload["result_row_count"] = row_count
                return payload
            except Exception as exc:  # pragma: no cover
                last_error = str(exc)
        raise RuntimeError(f"Query failed after retries: {last_error}")
