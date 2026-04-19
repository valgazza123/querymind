"""Initial migration for QueryMind core."""
from django.db import migrations, models


class Migration(migrations.Migration):
    """Create the query log table."""

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="QueryLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_input", models.TextField()),
                ("generated_sql", models.TextField()),
                ("explanation", models.TextField(blank=True)),
                ("execution_status", models.CharField(max_length=32)),
                ("execution_time_ms", models.PositiveIntegerField(default=0)),
                ("result_row_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"], "db_table": "query_log"},
        ),
        migrations.CreateModel(
            name="EtlLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("run_started_at", models.DateTimeField(auto_now_add=True)),
                ("run_finished_at", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(max_length=20)),
                ("records_loaded", models.PositiveIntegerField(default=0)),
                ("last_processed_enrollment_id", models.BigIntegerField(blank=True, null=True)),
                ("message", models.TextField(blank=True)),
            ],
            options={"ordering": ["-run_started_at"], "db_table": "etl_log"},
        ),
    ]
