from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.posts import router as posts_router
from .api.templates import router as templates_router
from .config import get_settings
from .schemas import AIConfigResponse

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="愛犬写真からInstagram向け投稿案を生成するAPI",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(posts_router)
app.include_router(templates_router)


@app.get("/api/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


@app.get("/api/config", response_model=AIConfigResponse, tags=["system"])
async def config() -> AIConfigResponse:
    return AIConfigResponse(
        image_provider=settings.image_ai_provider,
        text_provider=settings.text_ai_provider,
    )
