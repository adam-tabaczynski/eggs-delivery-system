from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.controllers.customers import router as customers_router
from src.controllers.cycles import router as cycles_router
from src.controllers.health import router as health_router
from src.exceptions import ConflictError, NotFoundError
from src.settings import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.include_router(health_router)
app.include_router(customers_router)
app.include_router(cycles_router)


@app.exception_handler(ConflictError)
def handle_conflict(_request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(NotFoundError)
def handle_not_found(_request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})
