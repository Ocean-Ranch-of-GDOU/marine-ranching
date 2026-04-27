from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.core.config import settings


router = APIRouter(tags=["dashboard-pages"])


@router.get("/", response_class=HTMLResponse)
async def dashboard_page() -> str:
    return settings.templates_dir.joinpath("dashboard.html").read_text(encoding="utf-8")
