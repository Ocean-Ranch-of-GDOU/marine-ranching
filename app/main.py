from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.dashboard_pages import router as dashboard_pages_router
from app.api.routes.dashboard_data import router as dashboard_data_router
from app.core.config import settings
from app.services.runtime_services import runtime_services


@asynccontextmanager
async def lifespan(_app: FastAPI):
    runtime_services.start()
    yield
    runtime_services.stop()


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
    )
    app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")
    app.mount("/resource", StaticFiles(directory=str(settings.base_dir / "resource")), name="resource")
    app.include_router(dashboard_pages_router)
    app.include_router(dashboard_data_router, prefix="/api")
    return app


app = create_application()
