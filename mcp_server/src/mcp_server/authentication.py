import base64
import logging
import os
import secrets

import click
from dotenv import load_dotenv
from loguru import logger
from passlib.context import CryptContext
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logging.getLogger("passlib").setLevel(logging.ERROR)
load_dotenv()

### CLI ###
@click.command()
@click.password_option()
def hash_password_cli(password: str) -> str:
    return hash_password(password=password, show_hashed_password=True)


def hash_password(password: str, show_hashed_password: bool = False) -> str:
    hashed_password: str = PWD_CONTEXT.hash(password)
    if show_hashed_password:
        print(f"Hashed password: {hashed_password}")
    return hashed_password


### Simple Basic Auth Middleware ###
PWD_CONTEXT: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


class BasicAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.username: str = os.getenv("MCP_USER", "admin")
        self.hashed_password: str = hash_password(password=os.getenv("MCP_PASSWORD", ""))

    def _verify_user(self, username: str) -> bool:
        return not self.username or secrets.compare_digest(username, self.username)

    def _verify_password(self, plain_password: str) -> bool:
        if not self.hashed_password:
            return True
        return PWD_CONTEXT.verify(plain_password, self.hashed_password)

    async def dispatch(self, request: Request, call_next) -> Response:
        auth_header: str = request.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            logger.warning("🔒 Kein Basic Auth Header")
            return Response(
                content="Basic authentication required",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="MCP Server"'},
            )

        try:
            encoded: str = auth_header.split(" ", 1)[1]
            decoded: str = base64.b64decode(encoded).decode("utf-8")
            username, password = decoded.split(":", 1)
            if self._verify_user(username) and self._verify_password(password):
                logger.info(f"✅ Basic Auth OK: {username}")
                request.state.user = username
                return await call_next(request)
            else:
                logger.warning(f"🔒 Falsche Credentials: {username}")
        except Exception as e:
            logger.warning(f"🔒 Basic Auth Error: {e}")
        return Response(
            content="Invalid credentials", status_code=401, headers={"WWW-Authenticate": 'Basic realm="MCP Server"'}
        )
