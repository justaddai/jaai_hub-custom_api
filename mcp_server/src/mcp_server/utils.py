from typing import Any

import httpx
from loguru import logger


async def call_external_api(endpoint: str) -> Any:
    try:
        response = await httpx.AsyncClient(timeout=30.0).get(endpoint)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError:
        logger.exception(f"Failed to call external API: {endpoint}")
        raise
