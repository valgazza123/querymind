"""Core data models for QueryMind."""
from __future__ import annotations

from django.db import models


class QueryLog(models.Model):
    """Stores a generated SQL attempt and its execution metadata."""

    user_input = models.TextField()
    generated_sql = models.TextField()
    explanation = models.TextField(blank=True)
    execution_status = models.CharField(max_length=32)
    execution_time_ms = models.PositiveIntegerField(default=0)
    result_row_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "query_log"

    def __str__(self) -> str:
        """Return a compact admin display string."""
        return f"{self.execution_status}: {self.user_input[:40]}"


class EtlLog(models.Model):
    """Tracks ETL pipeline runs for the analytics schema."""

    run_started_at = models.DateTimeField(auto_now_add=True)
    run_finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20)
    records_loaded = models.PositiveIntegerField(default=0)
    last_processed_enrollment_id = models.BigIntegerField(null=True, blank=True)
    message = models.TextField(blank=True)

    class Meta:
        ordering = ["-run_started_at"]
        db_table = "etl_log"

    def __str__(self) -> str:
        """Return a compact admin display string."""
        return f"{self.status} ({self.records_loaded})"
