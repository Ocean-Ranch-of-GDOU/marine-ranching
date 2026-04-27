from fastapi import APIRouter

from app.models.dashboard_models import DashboardPayload, DashboardState, UpdateResponse
from app.services.dashboard_service import dashboard_service


router = APIRouter(tags=["dashboard-data"])


@router.get("/dashboard", response_model=DashboardState)
async def get_dashboard_data() -> DashboardState:
    return DashboardState.model_validate(dashboard_service.get_dashboard_state())


@router.get("/example-payload", response_model=DashboardPayload)
async def get_example_payload() -> DashboardPayload:
    return DashboardPayload.model_validate(dashboard_service.get_example_payload())


@router.post("/payload", response_model=UpdateResponse)
async def receive_payload(payload: DashboardPayload) -> UpdateResponse:
    state = dashboard_service.apply_payload(payload)
    return UpdateResponse(ok=True, updated_at=state["updated_at"])
