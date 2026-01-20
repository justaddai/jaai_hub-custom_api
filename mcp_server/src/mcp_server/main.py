import os
from typing import Any

from fastmcp import FastMCP
from loguru import logger
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from mcp_server.authentication import ApiKeyAuthMiddleware
from mcp_server.utils import call_external_api

mcp: FastMCP = FastMCP(name="Externe APIs MCP Server")


@mcp.custom_route("/health", methods=["GET"])
async def get_mcp_server_healthcheck(_: Request) -> PlainTextResponse:
    return PlainTextResponse("OK", status_code=200)


@mcp.tool()
async def cat_fact() -> str:
    """Holt einen interessanten Fakt über Katzen"""
    result: dict[str, Any] = await call_external_api("https://catfact.ninja/fact")
    response: str = f"🐱 **Katzenfakt:** {result['fact']}"
    logger.info(f"🔍 Cat Fact: {response}")
    return response


@mcp.tool()
async def dog_image() -> str:
    """Holt ein zufälliges Hundebild"""
    result: dict[str, Any] = await call_external_api("https://dog.ceo/api/breeds/image/random")
    response: str = f"🐕 **Hundebild:** {result['message']}\n\n📊 **Status:** {result['status']}"
    logger.info(f"🔍 Dog Image: {response}")
    return response


def main() -> None:
    port: int = int(os.getenv("MCP_PORT", "8001"))
    logger.info("🚀 Starte JAAI Hub MCP Server für externe APIs")
    logger.info(f"🌐 Server läuft auf Port {port}")
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port,
        path="/",
        log_level="info",
        middleware=[(ApiKeyAuthMiddleware, [], {})],
    )


if __name__ == "__main__":
    main()
