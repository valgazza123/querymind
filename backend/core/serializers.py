"""Serializers for QueryMind API responses."""
from __future__ import annotations

from rest_framework import serializers

from .models import EtlLog, QueryLog


class QueryRequestSerializer(serializers.Serializer):
    """Input payload for natural-language queries."""

    natural_language = serializers.CharField()
    prior_sql = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class InsertRecordSerializer(serializers.Serializer):
    """Input payload for inserting a single record into a whitelisted table."""

    table_name = serializers.CharField()
    record = serializers.DictField(
        child=serializers.JSONField(),
        allow_empty=False,
    )


class QueryLogSerializer(serializers.ModelSerializer):
    """Serialized representation of query history."""

    class Meta:
        model = QueryLog
        fields = (
            "id",
            "user_input",
            "generated_sql",
            "explanation",
            "execution_status",
            "execution_time_ms",
            "result_row_count",
            "created_at",
        )


class EtlLogSerializer(serializers.ModelSerializer):
    """Serialized representation of ETL runs."""

    class Meta:
        model = EtlLog
        fields = (
            "id",
            "run_started_at",
            "run_finished_at",
            "status",
            "records_loaded",
            "last_processed_enrollment_id",
            "message",
        )
