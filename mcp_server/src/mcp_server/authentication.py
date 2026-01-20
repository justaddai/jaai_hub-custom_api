import os
import secrets

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.api_key = os.getenv("MCP_API_KEY", "")
        if not self.api_key:
            logger.warning("⚠️ MCP_API_KEY nicht gesetzt!")

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.api_key:
            return await call_next(request)
        if request.url.path == "/health":
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else ""
        if token and secrets.compare_digest(token, self.api_key):
            logger.info("✅ Auth OK")
            return await call_next(request)

        logger.warning("🔒 Auth fehlgeschlagen")
        return Response("Unauthorized", status_code=401)
