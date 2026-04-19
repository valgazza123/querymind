"""ASGI config for QueryMind."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "querymind_api.settings")

application = get_asgi_application()

