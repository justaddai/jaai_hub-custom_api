from fastapi import APIRouter
from loguru import logger

APP: APIRouter = APIRouter()


@APP.get("/health", status_code=201)
async def get_custom_api_healthcheck() -> bool:
    logger.info("Healthcheck called")
    return True
