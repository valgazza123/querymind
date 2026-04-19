"""App configuration for QueryMind core."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Core app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

