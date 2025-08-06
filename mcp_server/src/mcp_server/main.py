import os
from typing import Any

from fastmcp import FastMCP
from loguru import logger

from mcp_server.utils import call_external_api

mcp: FastMCP = FastMCP("Externe APIs MCP Server")

# MCP Tools mit FastMCP-Dekoratoren
@mcp.tool()
async def random_quote() -> str:
    """Holt ein zufälliges inspirierendes Zitat"""
    result: dict[str, Any] = await call_external_api("https://api.quotable.io/random")
    return f"📝 **Zitat:** \"{result['content']}\"\n\n👤 **Autor:** {result['author']}\n\n🏷️ **Tags:** {', '.join(result.get('tags', []))}"


@mcp.tool()
async def cat_fact() -> str:
    """Holt einen interessanten Fakt über Katzen"""
    result: dict[str, Any] = await call_external_api("https://catfact.ninja/fact")
    return f"🐱 **Katzenfakt:** {result['fact']}"


@mcp.tool()
async def dog_image() -> str:
    """Holt ein zufälliges Hundebild"""
    result: dict[str, Any] = await call_external_api("https://dog.ceo/api/breeds/image/random")
    return f"🐕 **Hundebild:** {result['message']}\n\n📊 **Status:** {result['status']}"


@mcp.tool()
async def advice() -> str:
    """Holt einen zufälligen Lebensratschlag"""
    result: dict[str, Any] = await call_external_api("https://api.adviceslip.com/advice")
    advice_text: str = result.get("slip", {}).get("advice", "")
    advice_id: int = result.get("slip", {}).get("id", 0)
    return f"💡 **Ratschlag #{advice_id}:** {advice_text}"


@mcp.tool()
async def posts(limit: int = 10) -> str:
    """Holt Demo-Posts von JSONPlaceholder"""
    posts_data: list[dict[str, Any]] = await call_external_api(
        f"https://jsonplaceholder.typicode.com/posts?_limit={min(limit, 100)}"
    )
    posts_text: str = f"📝 **{len(posts_data)} Demo-Posts:**\n\n"
    for post in posts_data[:5]:  # Zeige nur die ersten 5 für bessere Lesbarkeit
        posts_text += f"**Post {post['id']}:** {post['title']}\n"
        posts_text += f"_{post['body'][:100]}..._ \n\n"
    if len(posts_data) > 5:
        posts_text += f"... und {len(posts_data) - 5} weitere Posts"
    return posts_text


@mcp.tool()
async def user_info(user_id: int) -> str:
    """Holt Benutzerinformationen von JSONPlaceholder (User ID: 1-10)"""
    if user_id < 1 or user_id > 10:
        return "❌ **Fehler:** Benutzer-ID muss zwischen 1 und 10 liegen"
    user: dict[str, Any] = await call_external_api(f"https://jsonplaceholder.typicode.com/users/{user_id}")
    user_text = f"👤 **Benutzer {user['id']}:**\n\n"
    user_text += f"**Name:** {user['name']} ({user['username']})\n"
    user_text += f"**Email:** {user['email']}\n"
    user_text += f"**Telefon:** {user['phone']}\n"
    user_text += f"**Website:** {user['website']}\n"
    user_text += f"**Firma:** {user['company']['name']}\n"
    user_text += f"**Adresse:** {user['address']['street']}, {user['address']['city']}"
    return user_text


@mcp.prompt()
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


@mcp.prompt()
async def user_profile(user_id: int) -> str:
    if user_id < 1 or user_id > 10:
        return "❌ **Fehler:** Benutzer-ID muss zwischen 1 und 10 liegen"

    user: dict[str, Any] = await call_external_api(f"https://jsonplaceholder.typicode.com/users/{user_id}")
    content: str = f"""
        👤 **Detailliertes Benutzerprofil** 👤
        **Vollständiger Name:** {user['name']}
        **Benutzername:** {user['username']}
        **Kontaktdaten:**
        - Email: {user['email']}
        - Telefon: {user['phone']}
        - Website: {user['website']}
        **Adresse:**
        - Straße: {user['address']['street']}
        - Suite: {user['address']['suite']}
        - Stadt: {user['address']['city']}
        - PLZ: {user['address']['zipcode']}
        - Geo: {user['address']['geo']['lat']}, {user['address']['geo']['lng']}
        **Firma:**
        - Name: {user['company']['name']}
        - Slogan: {user['company']['catchPhrase']}
        - Geschäft: {user['company']['bs']}"""
    return content


def main() -> None:
    port: int = int(os.getenv("MCP_PORT", "8001"))
    logger.info(f"🚀 Starte JAAI Hub MCP Server für externe APIs")
    logger.info(f"🌐 Server läuft auf Port {port}")
    mcp.run(transport="http", host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
