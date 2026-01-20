import os
from datetime import datetime, timedelta
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
    return f"🐱 **Katzenfakt:** {result['fact']}"


@mcp.tool()
async def dog_image() -> str:
    """Holt ein zufälliges Hundebild"""
    result: dict[str, Any] = await call_external_api("https://dog.ceo/api/breeds/image/random")
    response: str = f"🐕 **Hundebild:** {result['message']}\n\n📊 **Status:** {result['status']}"
    logger.info(f"🔍 Dog Image: {response}")
    return response


@mcp.tool()
async def get_my_profile(idp_token: str = "") -> str:
    """Holt das Microsoft-Profil des eingeloggten Users (Name, E-Mail, etc.)"""
    if not idp_token:
        return "❌ Kein IDP Token verfügbar. Bitte via Microsoft einloggen."

    result: dict[str, Any] = await call_external_api(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {idp_token}"},
    )
    return (
        f"👤 **Microsoft Profil:**\n"
        f"- **Name:** {result.get('displayName', 'N/A')}\n"
        f"- **Vorname:** {result.get('givenName', 'N/A')}\n"
        f"- **Nachname:** {result.get('surname', 'N/A')}\n"
        f"- **E-Mail:** {result.get('mail') or result.get('userPrincipalName', 'N/A')}\n"
        f"- **Job:** {result.get('jobTitle', 'N/A')}"
    )


@mcp.tool()
async def get_my_calendar(idp_token: str = "", days: int = 7) -> str:
    """Holt Kalendereinträge für die nächsten Tage"""
    if not idp_token:
        return "❌ Kein IDP Token verfügbar. Bitte via Microsoft einloggen."

    start: str = datetime.utcnow().isoformat() + "Z"
    end: str = (datetime.utcnow() + timedelta(days=days)).isoformat() + "Z"
    result: dict[str, Any] = await call_external_api(
        f"https://graph.microsoft.com/v1.0/me/calendarView?startDateTime={start}&endDateTime={end}&$orderby=start/dateTime&$select=subject,start,end,location",
        headers={"Authorization": f"Bearer {idp_token}"},
    )

    events: list[dict[str, Any]] = result.get("value", [])
    if not events:
        return f"📅 Keine Termine in den nächsten {days} Tagen."

    lines: list[str] = []
    for event in events:
        subject: str = event.get("subject", "(Kein Titel)")
        start_dt: str = event.get("start", {}).get("dateTime", "")[:16].replace("T", " ")
        location: str = event.get("location", {}).get("displayName", "")
        loc_str: str = f" 📍 {location}" if location else ""
        lines.append(f"- **{subject}**\n  🕐 {start_dt}{loc_str}")
    return f"📅 **Termine der nächsten {days} Tage ({len(events)}):**\n\n" + "\n\n".join(lines)


@mcp.tool()
async def get_todays_meetings(idp_token: str = "") -> str:
    """Holt alle Termine für heute"""
    if not idp_token:
        return "❌ Kein IDP Token verfügbar. Bitte via Microsoft einloggen."

    today = datetime.utcnow().date()
    start: str = datetime(today.year, today.month, today.day).isoformat() + "Z"
    end: str = (datetime(today.year, today.month, today.day) + timedelta(days=1)).isoformat() + "Z"
    result: dict[str, Any] = await call_external_api(
        f"https://graph.microsoft.com/v1.0/me/calendarView?startDateTime={start}&endDateTime={end}&$orderby=start/dateTime&$select=subject,start,end,location,isAllDay",
        headers={"Authorization": f"Bearer {idp_token}"},
    )

    events: list[dict[str, Any]] = result.get("value", [])
    if not events:
        return "📅 Heute keine Termine! 🎉"

    lines: list[str] = []
    for event in events:
        subject: str = event.get("subject", "(Kein Titel)")
        if event.get("isAllDay"):
            time_str: str = "Ganztägig"
        else:
            start_time: str = event.get("start", {}).get("dateTime", "")[11:16]
            end_time: str = event.get("end", {}).get("dateTime", "")[11:16]
            time_str = f"{start_time} - {end_time}"
        location: str = event.get("location", {}).get("displayName", "")
        loc_str: str = f" 📍 {location}" if location else ""
        lines.append(f"- **{subject}**\n  🕐 {time_str}{loc_str}")
    return f"📅 **Heute ({len(events)} Termine):**\n\n" + "\n\n".join(lines)


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
