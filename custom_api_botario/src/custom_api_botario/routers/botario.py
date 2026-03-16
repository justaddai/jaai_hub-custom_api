import asyncio
import json

import httpx
from fastapi import APIRouter, Header, Path
from fastapi.responses import StreamingResponse
from jaai_hub.custom_api import ChatCompletionRequest
from jaai_hub.streaming_message import SourceGenType, Status, StreamingMessage
from loguru import logger

from custom_api_botario.models import (
    BotarioCompletion,
    BotarioCompletionPayload,
    BotarioResponse,
)

router: APIRouter = APIRouter(
    tags=["botario"],
    responses={404: {"description": "Not found"}},
)


def get_botario_url(botario_host: str, bot_id: str) -> str:
    """Build the Botario API URL with the given host and bot_id"""
    return f"https://{botario_host}/api/bots/{bot_id}/chats/send-message"


async def call_botario_api(message: str, session_id: str, botario_host: str, bot_id: str) -> BotarioResponse:
    """Call the Botario API and return the response"""
    url: str = get_botario_url(botario_host, bot_id)
    logger.debug(f"🤖 Calling Botario API at {url}")

    payload: BotarioCompletion = BotarioCompletion(
        payload=BotarioCompletionPayload(type="text", text=message),
        sessionId=session_id,
        startUrl="",
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload.model_dump())
        response.raise_for_status()

        # Botario returns line-delimited JSON, parse each line
        lines = response.text.strip().split("\n")
        for line in lines:
            if line.strip():
                data = json.loads(line)
                bot_response = BotarioResponse.model_validate(data)
                # Return the first response with text content
                if bot_response.payload.text:
                    return bot_response

        # If no response with text found, return the last one
        return BotarioResponse.model_validate(json.loads(lines[-1]))


@router.post("/{botario_host}/{bot_id}/chat/completions")
async def chat_completion(
    request: ChatCompletionRequest,
    botario_host: str = Path(example="bm.test.genai.justadd.ai"),
    bot_id: str = Path(example="69385b11097677787aea64ec"),
    session_id: str = Header(..., alias="X-Session-ID", description="Session ID for the Botario chat session"),
) -> StreamingResponse:
    """Chat completion endpoint for Botario with streaming support"""
    logger.info(f"🤖 Received Botario request for bot {bot_id} at {botario_host} with {len(request.messages)} messages")

    # Botario always streams - ignore the stream parameter
    return StreamingResponse(
        StreamingMessage(stream_botario_response(request, session_id, botario_host, bot_id)),
        media_type="text/event-stream",
    )


def extract_text_from_response(response: BotarioResponse) -> str:
    """Extracts plain text from a BotarioResponse"""
    return response.payload.text


async def stream_botario_response(
    request: ChatCompletionRequest, session_id: str, botario_host: str, bot_id: str
) -> SourceGenType:
    """Generate streaming response for Botario"""
    logger.info(f"🤖 Starting Botario workflow for bot {bot_id} at {botario_host}")

    # Get message from the last user message
    last_message: str = request.messages[-1].content if request.messages else ""
    logger.debug(f"🤖 Message text length: {len(last_message)} characters")
    if not last_message.strip():
        yield "❌ **Fehler:** Bitte geben Sie eine Nachricht ein."
        return

    try:
        yield Status(type="basic", text="🤖 Verarbeite Anfrage...")
        await asyncio.sleep(0.3)

        # Call Botario API
        botario_response: BotarioResponse = await call_botario_api(last_message, session_id, botario_host, bot_id)
        response_text: str = extract_text_from_response(botario_response)

        yield response_text

        yield Status(type="complete", text="✅ Fertig!")
        logger.success("🤖 Botario workflow completed successfully")

    except Exception as error:
        logger.exception("🤖 Botario request failed")
        yield f"❌ **Fehler:** {str(error)}"
