import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from jaai_hub.custom_api import ChatCompletionRequest
from jaai_hub.streaming_message import SourceGenType, Status, StreamingMessage
from loguru import logger

from custom_api.llm.recipe import RecipeAssistant, RecipeResult

router: APIRouter = APIRouter(
    tags=["recipe_assistant"],
    responses={404: {"description": "Not found"}},
)


@router.post("/chat/completions")
async def chat_completion(request: ChatCompletionRequest) -> StreamingResponse:
    """Chat completion endpoint for recipe generation with streaming support"""
    logger.info(f"🍳 Received recipe request with {len(request.messages)} messages")
    logger.debug(f"🍳 Request model: {request.model}, stream: {request.stream}")
    if request.stream:
        logger.info("🍳 Starting streaming response for recipe generation")
        return StreamingResponse(StreamingMessage(stream_recipe_response(request)), media_type="text/event-stream")
    else:
        logger.warning("🍳 Non-streaming requests not supported for recipe generation")
        raise HTTPException(status_code=400, detail="Streaming is required for recipe generation")


def format_recipe_as_markdown(recipe: RecipeResult) -> str:
    """Formatiert das Rezept als schönes Markdown"""

    difficulty_emoji: str = {"Einfach": "🟢", "Mittel": "🟡", "Schwer": "🔴"}.get(recipe.difficulty, "⚪")
    markdown: str = f"""# 🍳 {recipe.recipe_name}

## 📝 Beschreibung
{recipe.description}

## ⏱️ Details
- **Zubereitungszeit:** {recipe.cooking_time}
- **Schwierigkeit:** {difficulty_emoji} {recipe.difficulty}

## 🛒 Zutaten
"""
    for ingredient in recipe.ingredients:
        markdown += f"- {ingredient}\n"

    markdown += f"""
## 👨‍🍳 Zubereitung
"""
    for i, instruction in enumerate(recipe.instructions, 1):
        markdown += f"{i}. {instruction}\n"

    markdown += f"""
## 💡 Kochtipps
"""
    for tip in recipe.tips:
        markdown += f"- 💡 {tip}\n"

    markdown += f"""
## 🥗 Nährwerte
{recipe.nutritional_info}

---
*Guten Appetit! 🍽️ Rezept erstellt von Ihrem KI-Kochassistenten* 🤖
"""

    return markdown


async def stream_recipe_response(request: ChatCompletionRequest) -> SourceGenType:
    """Generate streaming response for recipe generation"""
    logger.info("🍳 Starting AI-powered recipe generation workflow")

    # Get ingredients from the last user message
    last_message: str = request.messages[-1].content if request.messages else ""
    logger.debug(f"🍳 Ingredients text length: {len(last_message)} characters")
    if not last_message.strip():
        yield "❌ **Fehler:** Bitte geben Sie Ihre verfügbaren Zutaten ein (z.B. 'Nudeln, Tomaten, Käse')."
        return

    # Initialize the recipe assistant
    try:
        yield Status(type="basic", text="🍳 Starte Kochassistent...")
        await asyncio.sleep(0.3)  # Brief processing time
        recipe_assistant: RecipeAssistant = RecipeAssistant.get_instance()
        logger.info("🍳 Recipe Assistant initialized successfully")
    except Exception as error:
        logger.exception(f"🍳 Failed to initialize recipe assistant")
        yield f"❌ **Fehler beim Starten des Kochassistenten:** {str(error)}"
        return

    # Generate the recipe
    try:
        yield Status(type="basic", text="👨‍🍳 Entwickle Rezept...")
        logger.info("🍳 Starting recipe generation")

        recipe_result: RecipeResult = await recipe_assistant.predict(
            ingredients=last_message, temperature=request.temperature or 0.3, timeout=5000
        )
        logger.success("🍳 Recipe generation completed successfully")

        yield Status(type="basic", text="📝 Formatiere Rezept...")
        await asyncio.sleep(0.2)

        # Format and yield the recipe as markdown
        formatted_recipe: str = format_recipe_as_markdown(recipe_result)
        yield formatted_recipe

        yield Status(type="complete", text="✅ Rezept fertig! Guten Appetit! 🍽️")
        logger.success("🍳 Recipe generation workflow completed successfully")

    except Exception as error:
        logger.exception(f"🍳 Recipe generation failed")
        yield f"❌ **Fehler bei der Rezepterstellung:** {str(error)}"
