"""Admin registrations for QueryMind core."""
from django.contrib import admin

from .models import EtlLog, QueryLog


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    """Admin configuration for query history."""

    list_display = ("id", "execution_status", "execution_time_ms", "result_row_count", "created_at")
    search_fields = ("user_input", "generated_sql", "explanation")
    list_filter = ("execution_status", "created_at")


@admin.register(EtlLog)
class EtlLogAdmin(admin.ModelAdmin):
    """Admin configuration for ETL logs."""

    list_display = ("id", "status", "records_loaded", "last_processed_enrollment_id", "run_started_at")
    list_filter = ("status", "run_started_at")
