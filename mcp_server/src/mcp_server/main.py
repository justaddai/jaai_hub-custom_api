import os
from typing import Any

from fastmcp import FastMCP
from loguru import logger

from mcp_server.utils import call_external_api

mcp: FastMCP = FastMCP("Externe APIs MCP Server")

# MCP Tools mit FastMCP-Dekoratoren
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


@mcp.tool()
async def advice() -> str:
    """Holt einen zufälligen Lebensratschlag"""
    result: dict[str, Any] = await call_external_api("https://api.adviceslip.com/advice")
    advice_text: str = result.get("slip", {}).get("advice", "")
    advice_id: int = result.get("slip", {}).get("id", 0)
    response: str = f"💡 **Ratschlag #{advice_id}:** {advice_text}"
    logger.info(f"🔍 Advice: {response}")
    return response


@mcp.tool()
async def daily_inspiration(include_animals: bool = True) -> str:
    """Erstellt eine tägliche Inspirationsnachricht mit Zitat und Fakten"""
    quote: dict[str, Any] = await call_external_api("https://api.quotable.io/random")
    advice_data: dict[str, Any] = await call_external_api("https://api.adviceslip.com/advice")

    content: str = f"🌟 **Tägliche Inspiration** 🌟\n\n"
    content += f"📝 **Zitat des Tages:**\n\"{quote['content']}\" - {quote['author']}\n\n"
    content += f"💡 **Ratschlag:**\n{advice_data['slip']['advice']}\n\n"
    if include_animals:
        cat_fact_data: dict[str, Any] = await call_external_api("https://catfact.ninja/fact")
        content += f"🐱 **Interessanter Fakt:**\n{cat_fact_data['fact']}\n\n"
    content += "✨ _Wünsche dir einen wunderbaren Tag!_ ✨"
    return content


def main() -> None:
    port: int = int(os.getenv("MCP_PORT", "8001"))
    logger.info(f"🚀 Starte JAAI Hub MCP Server für externe APIs")
    logger.info(f"🌐 Server läuft auf Port {port}")
    mcp.run(transport="http", host="0.0.0.0", port=port, path="/mcp", log_level="info")


if __name__ == "__main__":
    main()
