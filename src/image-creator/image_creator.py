import json
import os

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from loguru import logger
from openai import Client
from jaai_hub.custom_api import (
    ChatCompletionRequest,
    health_check_endpoint,
)
from jaai_hub.streaming_message import (
    GeneratedImage,
    SourceGenType,
    Status,
    StreamingMessage,
)

# Create router instead of app
router = APIRouter(
    tags=["image_creator"],  # This helps with API documentation
    responses={404: {"description": "Not found"}},
)


@router.get("/health")
async def health():
    """Health check endpoint"""
    return health_check_endpoint("image-creator-api")


@router.post("/chat/completions")
async def chat_completion(request: ChatCompletionRequest):
    """Chat completion endpoint with streaming support for image generation"""
    logger.info(f"🎨 Received chat completion request with {len(request.messages)} messages")
    logger.debug(f"🎨 Request model: {request.model}, stream: {request.stream}")

    if request.stream:
        logger.info("🎨 Starting streaming response for image generation")
        return StreamingResponse(
            StreamingMessage(stream_image_generation_response(request)), media_type="text/event-stream"
        )
    else:
        logger.warning("🎨 Non-streaming requests not supported for image generation")
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Streaming is required for image generation")


def create_image(prompt: str, width: int = 1024, height: int = 1024, num_images: int = 1):
    logger.info(f"🖼️ Creating {num_images} image(s) with FLUX.1-dev")
    logger.debug(f"🖼️ Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    logger.debug(f"🖼️ Dimensions: {width}x{height}")

    api_key = os.environ.get("TOGETHER_API_KEY")
    if not api_key:
        logger.error("🖼️ TOGETHER_API_KEY not found in environment variables")
        raise ValueError("TOGETHER_API_KEY environment variable is required")

    logger.debug("🖼️ Initializing Together AI client")
    client = Client(
        api_key=api_key,
        base_url="https://api.together.xyz/v1",
    )

    try:
        logger.info("🖼️ Sending image generation request to Together AI")
        result = client.images.generate(
            model="black-forest-labs/FLUX.1-dev",
            prompt=prompt,
            n=num_images,
            extra_body={"width": width, "height": height},
            response_format="b64_json",
        )

        b64_strings = [data.b64_json for data in result.data]
        logger.success(f"🖼️ Successfully generated {len(b64_strings)} image(s)")
        logger.debug(f"🖼️ Image data lengths: {[len(img) for img in b64_strings]}")

        return b64_strings

    except Exception as e:
        logger.error(f"🖼️ Failed to generate image: {str(e)}")
        raise


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_image",
            "description": "Create an image based on a prompt.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "A highly optimized prompt for image generation. In English.",
                    },
                    "width": {
                        "type": "integer",
                        "description": "The width of the image to generate. Must be between 256 and 1024. Default is 512.",
                    },
                    "height": {
                        "type": "integer",
                        "description": "The height of the image to generate. Must be between 256 and 1024. Default is 512.",
                    },
                    "num_images": {
                        "type": "integer",
                        "description": "The number of images to generate. Must be between 1 and 10. Default is 1.",
                    },
                },
                "required": ["prompt", "width", "height", "num_images"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
]


def _initialize_llm_client():
    """Initialize and return LiteLLM client with environment validation."""
    lite_llm_url = os.getenv("LITE_LLM_URL")
    lite_llm_key = os.getenv("LITE_LLM_API_KEY")

    if not lite_llm_url or not lite_llm_key:
        logger.error("🤖 LiteLLM credentials not found in environment")
        raise ValueError("LiteLLM configuration missing")

    logger.debug(f"🤖 Connecting to LiteLLM at {lite_llm_url}")
    return Client(base_url=lite_llm_url, api_key=lite_llm_key)


def _get_image_generation_system_prompt() -> str:
    """Return the system prompt for image generation."""
    return (
        "You are an expert image creator and advisor. You can help create images through "
        "text-to-image generation and provide detailed advice on optimizing image prompts. "
        "You'll analyze your request and either create an image directly or help improve "
        "your image generation prompts. You aim to understand the visual elements you want "
        "and translate them into effective prompts that capture your vision."
    )


async def _request_image_generation_from_ai(client: Client, messages: list) -> dict:
    """Request GPT-4o to analyze and potentially generate images."""
    logger.info("🤖 Requesting GPT-4o to analyze image generation request")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": _get_image_generation_system_prompt()},
                *[{"role": msg.role, "content": msg.content} for msg in messages],
            ],
            stream=False,
            tools=TOOLS,
            tool_choice="auto",
        )
        logger.debug("🤖 Received response from GPT-4o")
        return response
    except Exception as e:
        logger.error(f"🤖 Failed to communicate with LiteLLM: {str(e)}")
        raise


async def _analyze_generated_images(client: Client, messages: list, images_b64: list) -> str:
    """Use GPT-4o to analyze the generated images."""
    logger.info("🔍 Starting AI image analysis")

    analysis_messages = [
        {"role": "system", "content": _get_image_generation_system_prompt()},
        *[{"role": msg.role, "content": msg.content} for msg in messages],
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Please analyze the generated image and provide feedback on how well it "
                        "matches the requested prompt. What aspects were captured successfully and "
                        "what could be improved? It is very important to answer in German."
                    ),
                },
                *[
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}
                    for img in images_b64
                ],
            ],
        },
    ]

    try:
        analysis_response = client.chat.completions.create(
            model="gpt-4o",
            messages=analysis_messages,
            stream=False,
        )

        result = analysis_response.choices[0].message.content
        logger.info("🔍 AI image analysis completed")
        logger.debug(f"🔍 Analysis: {result[:100]}{'...' if len(result) > 100 else ''}")
        return result

    except Exception as e:
        logger.error(f"🔍 Image analysis failed: {str(e)}")
        return f"Bildanalyse konnte nicht durchgeführt werden: {str(e)}"


async def _process_image_tool_call(tool_call: dict, messages: list, client: Client):
    """Process a create_image tool call and yield results."""
    logger.info("🤖 AI wants to create an image - parsing arguments")
    yield Status(type="basic", text="🖼️ Erstelle Bilder...")

    try:
        args = json.loads(tool_call.function.arguments)
        logger.debug(f"🤖 Image generation args: {args}")

        # Generate images
        images_b64 = create_image(**args)

        # Yield generated images
        logger.info(f"🎨 Yielding {len(images_b64)} generated image(s)")
        for i, image_b64 in enumerate(images_b64):
            logger.debug(f"🎨 Processing image {i+1}/{len(images_b64)}")
            image_data = GeneratedImage(
                url=f"data:image/png;base64,{image_b64}",
                prompt=args["prompt"],
                width=args["width"],
                height=args["height"],
            )
            yield image_data

        # Analyze images
        yield Status(type="basic", text="💬 Analyse des Bildes...")
        analysis_result = await _analyze_generated_images(client, messages, images_b64)
        yield analysis_result

        yield Status(type="complete", text="🎨 Fertig!")
        logger.success("🎨 Image generation workflow completed successfully")

    except Exception as e:
        logger.error(f"🤖 Tool call execution failed: {str(e)}")
        yield f"Error during image generation: {str(e)}"


async def stream_image_generation_response(request: ChatCompletionRequest) -> SourceGenType:
    """Generate streaming response for image generation queries."""
    logger.info("🤖 Starting AI-powered image generation workflow")

    # Get last user message for context
    last_message = request.messages[-1].content if request.messages else ""
    logger.debug(f"🤖 User request: {last_message[:200]}{'...' if len(last_message) > 200 else ''}")

    # Initialize LLM client
    try:
        client = _initialize_llm_client()
    except ValueError as e:
        yield f"Error: {str(e)}"
        return

    # Request AI analysis and potential image generation
    try:
        extraction_response = await _request_image_generation_from_ai(client, request.messages)
    except Exception as e:
        yield f"Error communicating with AI service: {str(e)}"
        return

    # Handle AI response text
    result = extraction_response.choices[0].message.content
    if result:
        logger.debug(f"🤖 AI response text: {result[:100]}{'...' if len(result) > 100 else ''}")
        yield result

    # Handle tool calls
    if extraction_response.choices[0].message.tool_calls:
        tool_calls = extraction_response.choices[0].message.tool_calls
        logger.info(f"🤖 AI requested {len(tool_calls)} tool call(s)")

        tool_call = tool_calls[0]
        if tool_call.function.name == "create_image":
            async for item in _process_image_tool_call(tool_call, request.messages, client):
                yield item
        else:
            logger.warning(f"🤖 Unknown tool call: {tool_call.function.name}")
            yield f"Unknown tool requested: {tool_call.function.name}"
    else:
        logger.info("🤖 AI provided response without tool calls")
        yield Status(type="complete", text="🎨 Fertig!")
