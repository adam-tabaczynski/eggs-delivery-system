from fastapi import FastAPI

from src.controllers.health import router as health_router
from src.settings import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.include_router(health_router)
