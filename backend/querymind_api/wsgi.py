"""WSGI config for QueryMind."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "querymind_api.settings")

application = get_wsgi_application()

