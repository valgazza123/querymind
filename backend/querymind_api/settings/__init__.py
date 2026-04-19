"""Default settings module for QueryMind.

Local development imports local settings by default. Production containers set
DJANGO_SETTINGS_MODULE=querymind_api.settings.production explicitly.
"""
from .local import *  # noqa: F401,F403
