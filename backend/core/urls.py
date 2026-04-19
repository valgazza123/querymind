"""URL routes for QueryMind core APIs."""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.api_root, name="api-root"),
    path("health", views.health, name="health"),
    path("schema", views.schema, name="schema"),
    path("schema/intelligence", views.schema_intelligence, name="schema-intelligence"),
    path("schema/relationship-preview", views.relationship_preview, name="relationship-preview"),
    path("records/insert", views.insert_schema_record, name="records-insert"),
    path("query", views.query, name="query"),
    path("query/stream", views.query_stream, name="query-stream"),
    path("query/explain", views.query_explain, name="query-explain"),
    path("query/fixit", views.query_fixit, name="query-fixit"),
    path("history", views.history, name="history"),
    path("history/<int:query_log_id>", views.query_detail, name="history-detail"),
    path("metrics", views.metrics, name="metrics"),
    path("analytics/rollup", views.analytics_rollup, name="analytics-rollup"),
    path("admin/etl/run", views.run_etl, name="admin-etl-run"),
]
