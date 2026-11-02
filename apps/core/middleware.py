import re
import uuid

from . import context

_VALID_ID = re.compile(r"^[A-Za-z0-9\-]{8,64}$")


class CorrelationIdMiddleware:
    """Atribui um correlation_id a cada requisição (aceita X-Request-ID válido do proxy)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.headers.get("X-Request-ID", "")
        correlation_id = incoming if _VALID_ID.match(incoming) else uuid.uuid4().hex
        request.correlation_id = correlation_id
        token_cid = context.set_correlation_id(correlation_id)
        # REMOTE_ADDR é definido pelo Gunicorn/Nginx; não confiar em X-Forwarded-For sem proxy configurado.
        token_ip = context.set_client_ip(request.META.get("REMOTE_ADDR"))
        try:
            response = self.get_response(request)
        finally:
            context.reset_correlation_id(token_cid)
            context.reset_client_ip(token_ip)
        response["X-Request-ID"] = correlation_id
        return response
