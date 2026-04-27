from app.models.dashboard_models import DashboardPayload, RealtimeMqttMessage
from app.repositories.dashboard_repository import dashboard_repository


class DashboardService:
    def get_dashboard_state(self) -> dict:
        return dashboard_repository.get_state()

    def get_example_payload(self) -> dict:
        return dashboard_repository.get_example_payload()

    def apply_payload(self, payload: DashboardPayload) -> dict:
        return dashboard_repository.update_from_payload(payload)

    def apply_realtime_message(self, message: RealtimeMqttMessage) -> dict:
        return dashboard_repository.update_from_realtime_message(message)

    def set_mqtt_enabled(self, enabled: bool) -> None:
        dashboard_repository.set_mqtt_enabled(enabled)


dashboard_service = DashboardService()
