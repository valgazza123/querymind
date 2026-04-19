"""API throttles for QueryMind."""
from rest_framework.throttling import SimpleRateThrottle


class QueryRateThrottle(SimpleRateThrottle):
    """Limit NL query requests to 10 per minute per IP."""

    scope = "querymind_query"

    def get_cache_key(self, request, view):
        """Build the throttle cache key from the client IP."""
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}

