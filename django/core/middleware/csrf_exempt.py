from django.utils.deprecation import MiddlewareMixin


class CSRFExemptAPIMiddleware(MiddlewareMixin):
    """
    Middleware to conditionally exempt API routes from CSRF validation.
    This must run before Django's CSRF middleware.
    """

    def process_request(self, request):
        # Only check API routes
        if not request.path.startswith("/api/"):
            return None

        # Exempt all API routes from CSRF validation
        setattr(request, "_dont_enforce_csrf_checks", True)
        return None
