from app.models.dashboard_models import DashboardPayload, RealtimeMqttMessage


class MqttPayloadMapper:
    def parse(
        self,
        payload: dict,
    ) -> DashboardPayload | RealtimeMqttMessage | None:
        if "stations" in payload:
            return DashboardPayload.model_validate(payload)

        if "device" in payload:
            supported_keys = {
                "water_temp",
                "do",
                "salinity",
                "wind_speed",
                "light",
                "flow_speed",
                "flow_dir",
                "remain_material",
            }
            if any(key in payload for key in supported_keys):
                return RealtimeMqttMessage.model_validate(payload)

        return None


mqtt_payload_mapper = MqttPayloadMapper()
