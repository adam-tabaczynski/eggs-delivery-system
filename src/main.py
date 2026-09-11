from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.controllers.customers import router as customers_router
from src.controllers.health import router as health_router
from src.exceptions import ConflictError
from src.settings import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.include_router(health_router)
app.include_router(customers_router)


@app.exception_handler(ConflictError)
def handle_conflict(_request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})
