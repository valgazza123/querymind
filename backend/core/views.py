"""API views for QueryMind."""
from __future__ import annotations

import json
import time

from django.http import StreamingHttpResponse
from django.db.utils import DatabaseError, IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .analytics import fetch_analytics_payload
from .etl import run_incremental_etl
from .models import QueryLog
from .serializers import InsertRecordSerializer, QueryLogSerializer, QueryRequestSerializer
from .services import (
    compute_metrics,
    explain_sql,
    get_query_log_detail,
    get_relationship_preview,
    get_schema_payload,
    get_table_intelligence,
    insert_record,
    repair_sql,
    run_querymind_query,
    stream_query_tokens,
)
from .throttles import QueryRateThrottle


@api_view(["GET"])
def api_root(_request) -> Response:
    """Return a simple API index."""
    return Response(
        {
            "name": "QueryMind API",
            "endpoints": {
                "query": "/api/query",
                "schema": "/api/schema",
                "schema_intelligence": "/api/schema/intelligence?table_name=student",
                "relationship_preview": "/api/schema/relationship-preview?from_table=student&from_column=department_id&to_table=department&to_column=department_id",
                "history": "/api/history",
                "analytics_rollup": "/api/analytics/rollup",
                "admin_etl_run": "/api/admin/etl/run",
                "query_stream": "/api/query/stream",
                "query_explain": "/api/query/explain",
                "query_fixit": "/api/query/fixit",
                "query_detail": "/api/history/<id>",
                "metrics": "/api/metrics",
                "health": "/api/health",
            },
        }
    )


@api_view(["GET"])
def health(_request) -> Response:
    """Return a health payload for local smoke tests."""
    return Response({"status": "ok"})


@api_view(["GET"])
def schema(_request) -> Response:
    """Return a compact schema representation for the frontend."""
    return Response(get_schema_payload())


@api_view(["GET"])
def schema_intelligence(request) -> Response:
    """Return row stats, samples, and metadata for a table."""
    table_name = request.GET.get("table_name", "").strip()
    if not table_name:
        return Response({"detail": "table_name is required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        return Response(get_table_intelligence(table_name))
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except DatabaseError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def relationship_preview(request) -> Response:
    """Return sample joined rows for a foreign-key pathway."""
    required = {
        "from_table": request.GET.get("from_table", "").strip(),
        "from_column": request.GET.get("from_column", "").strip(),
        "to_table": request.GET.get("to_table", "").strip(),
        "to_column": request.GET.get("to_column", "").strip(),
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        return Response({"detail": f"Missing parameters: {', '.join(missing)}"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        return Response(get_relationship_preview(**required))
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except DatabaseError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def insert_schema_record(request) -> Response:
    """Insert a single record into a whitelisted public table."""
    serializer = InsertRecordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        inserted = insert_record(
            table_name=serializer.validated_data["table_name"],
            record=serializer.validated_data["record"],
        )
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except (IntegrityError, DatabaseError) as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"status": "inserted", "row": inserted}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def query(request) -> Response:
    """Accept a natural-language query and return a SQL result."""
    for throttle in [QueryRateThrottle()]:
        if not throttle.allow_request(request, query):
            return Response({"detail": "Rate limit exceeded."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

    serializer = QueryRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    natural_language = serializer.validated_data["natural_language"]
    prior_sql = serializer.validated_data.get("prior_sql") or None
    try:
        generated = run_querymind_query(natural_language, prior_sql=prior_sql)
    except Exception as exc:
        log = QueryLog.objects.create(
            user_input=natural_language,
            generated_sql=prior_sql or "",
            explanation=str(exc),
            execution_status="failed",
            execution_time_ms=0,
            result_row_count=0,
        )
        return Response(
            {
                "detail": str(exc),
                "query_log_id": log.id,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    log = QueryLog.objects.create(
        user_input=natural_language,
        generated_sql=str(generated["sql"]),
        explanation=str(generated["explanation"]),
        execution_status="success",
        execution_time_ms=int(generated["execution_time"]),
        result_row_count=len(generated["results"]),
    )
    generated["query_log_id"] = log.id

    return Response(generated, status=status.HTTP_200_OK)


@api_view(["POST"])
def query_explain(request) -> Response:
    """Return EXPLAIN (FORMAT JSON) for a validated SQL string."""
    raw_sql = (request.data or {}).get("sql", "")
    try:
        plan = explain_sql(raw_sql)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except DatabaseError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(plan)


@api_view(["POST"])
def query_fixit(request) -> Response:
    """Repair a failing SQL statement and return the corrected version."""
    payload = request.data or {}
    failing_sql = payload.get("sql", "")
    error_message = payload.get("error", "")
    natural_language = payload.get("natural_language", "")
    try:
        return Response(repair_sql(failing_sql, error_message, natural_language))
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except DatabaseError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def metrics(_request) -> Response:
    """Return live metrics aggregated from the query log."""
    return Response(compute_metrics())


@api_view(["GET"])
def query_detail(_request, query_log_id: int) -> Response:
    """Return a single QueryLog record by id, used for share-link hydration."""
    try:
        return Response(get_query_log_detail(query_log_id))
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
def history(request) -> Response:
    """Return paginated query history records."""
    paginator = PageNumberPagination()
    paginator.page_size = 10
    queryset = QueryLog.objects.all()
    page = paginator.paginate_queryset(queryset, request)
    serializer = QueryLogSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
def analytics_rollup(_request) -> Response:
    """Return chart-ready rollup data from the analytics schema."""
    return Response(fetch_analytics_payload())


@api_view(["POST"])
def run_etl(_request) -> Response:
    """Trigger the incremental ETL pipeline."""
    try:
        result = run_incremental_etl()
        return Response(
            {
                "status": result.status,
                "records_loaded": result.records_loaded,
                "last_processed_enrollment_id": result.last_processed_enrollment_id,
                "message": result.message,
            }
        )
    except Exception as exc:
        return Response(
            {
                "status": "failed",
                "records_loaded": 0,
                "last_processed_enrollment_id": None,
                "message": str(exc),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def query_stream(request) -> StreamingHttpResponse:
    """Stream live SSE chunks of a real generated query for the typewriter overlay."""
    natural_language = request.GET.get("natural_language", "").strip()
    if not natural_language:
        natural_language = "Show top 10 students by GPA"

    def event_stream():
        try:
            for payload in stream_query_tokens(natural_language):
                yield f"data: {json.dumps(payload, default=str)}\n\n"
                time.sleep(0.04)
        except Exception as exc:  # pragma: no cover
            yield f"data: {json.dumps({'stage': 'error', 'token': str(exc)})}\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
