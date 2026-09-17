from fastapi import FastAPI

from src.controllers.customers import router as customers_router
from src.controllers.cycles import router as cycles_router
from src.controllers.health import router as health_router
from src.controllers.integrations.fast_api.error_handlers import (
    register_exception_handlers,
)
from src.settings import get_settings

__all__ = ["fastapi_app"]

settings = get_settings()

fastapi_app = FastAPI(title=settings.app_name)

fastapi_app.include_router(health_router)
fastapi_app.include_router(customers_router)
fastapi_app.include_router(cycles_router)
register_exception_handlers(fastapi_app)
