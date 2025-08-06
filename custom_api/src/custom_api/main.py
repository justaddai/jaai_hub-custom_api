import os
import sys
from typing import Any

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from loguru import logger

from custom_api import __version__ as API_VERSION
from custom_api.authentication import verify_basic_auth
from custom_api.routers.healthcheck import APP as healthcheck_router
from custom_api.routers.recipe import router as recipe_assistant_router

# Configure loguru
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)

# Create main FastAPI application
app: FastAPI = FastAPI(
    title="JAAI Hub Custom API Example",
    description="API showcasing the JAAI Hub Custom API features",
    version=API_VERSION,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Add auth protection to documentation
@app.get("/docs", include_in_schema=False)
async def get_documentation(_: str = Depends(verify_basic_auth)) -> HTMLResponse:
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


@app.get("/redoc", include_in_schema=False)
async def get_redoc_documentation(_: str = Depends(verify_basic_auth)) -> HTMLResponse:
    return get_redoc_html(openapi_url="/openapi.json", title="docs")


@app.get("/openapi.json", include_in_schema=False)
async def openapi(_: str = Depends(verify_basic_auth)) -> dict[str, Any]:
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        contact=app.contact,
        routes=app.routes,
        tags=app.openapi_tags,
    )


@app.get("/", include_in_schema=False)
async def read_root(_: str = Depends(verify_basic_auth)) -> dict[str, str]:
    return {"JAAI Hub Custom API Example": API_VERSION}


# Mount the routers
app.include_router(healthcheck_router, tags=["Healthcheck"], dependencies=[Depends(verify_basic_auth)])
app.include_router(recipe_assistant_router, tags=["Recipe Assistant"], dependencies=[Depends(verify_basic_auth)])


def main() -> None:
    port: int = int(os.getenv("CUSTOM_API_PORT", "8000"))
    logger.info(f"Starting JAAI Hub Custom API server on port {port}")
    uvicorn.run(
        "custom_api.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
