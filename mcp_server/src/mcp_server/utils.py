from typing import Any

import httpx
from loguru import logger


async def call_external_api(endpoint: str, headers: dict[str, str] | None = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"API call failed: {endpoint} - {e.response.status_code}: {e.response.text}")
        raise
