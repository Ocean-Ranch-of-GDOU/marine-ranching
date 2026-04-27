import json
import logging
import ssl
import time

from pydantic import ValidationError

from app.core.config import settings
from app.services.dashboard_service import dashboard_service
from app.services.mqtt_payload_mapper import mqtt_payload_mapper

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover
    mqtt = None


logger = logging.getLogger("uvicorn.error")


def _reason_code_value(reason_code) -> int | str:
    if hasattr(reason_code, "value"):
        return reason_code.value
    return reason_code


class MqttConsumerService:
    def __init__(self) -> None:
        self._client = None

    def start(self) -> None:
        if mqtt is None or not settings.mqtt_enabled:
            if mqtt is None:
                logger.warning("MQTT client not available: paho-mqtt is not installed.")
            else:
                logger.info("MQTT disabled: broker/topic configuration is incomplete.")
            return

        client_id = settings.mqtt_client_id or f"ocean-dashboard-{int(time.time())}"
        logger.info(
            "Starting MQTT client. broker=%s port=%s topic=%s tls=%s keepalive=%s client_id=%s",
            settings.mqtt_broker,
            settings.mqtt_port,
            settings.mqtt_topic,
            settings.mqtt_use_tls,
            settings.mqtt_keepalive,
            client_id,
        )
        self._client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv5)

        if settings.mqtt_username:
            self._client.username_pw_set(
                username=settings.mqtt_username,
                password=settings.mqtt_password,
            )
            logger.info("Configured MQTT username authentication. username=%s", settings.mqtt_username)

        if settings.mqtt_use_tls:
            self._client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
            if settings.mqtt_tls_insecure:
                self._client.tls_insecure_set(True)
            logger.info("Configured MQTT TLS. insecure=%s", settings.mqtt_tls_insecure)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._client.on_subscribe = self._on_subscribe
        self._client.connect_async(
            settings.mqtt_broker,
            settings.mqtt_port,
            keepalive=settings.mqtt_keepalive,
        )
        logger.info("Issued async MQTT connect request.")
        self._client.loop_start()

    def stop(self) -> None:
        if self._client is None:
            return
        logger.info("Stopping MQTT client.")
        self._client.loop_stop()
        self._client.disconnect()
        self._client = None

    def _on_connect(self, client, _userdata, _flags, reason_code, _properties=None) -> None:
        resolved_reason_code = _reason_code_value(reason_code)
        if resolved_reason_code == 0 and settings.mqtt_topic:
            logger.info(
                "MQTT connected successfully. broker=%s port=%s topic=%s",
                settings.mqtt_broker,
                settings.mqtt_port,
                settings.mqtt_topic,
            )
            client.subscribe(settings.mqtt_topic)
            dashboard_service.set_mqtt_enabled(True)
            return

        logger.error("MQTT connection failed. reason_code=%s", resolved_reason_code)

    def _on_disconnect(self, _client, _userdata, _disconnect_flags, _reason_code, _properties=None) -> None:
        dashboard_service.set_mqtt_enabled(False)
        logger.warning("MQTT disconnected. reason_code=%s", _reason_code_value(_reason_code))

    def _on_subscribe(self, _client, _userdata, mid, reason_code_list, _properties=None) -> None:
        logger.info(
            "MQTT subscribed successfully. mid=%s reason_codes=%s",
            mid,
            [_reason_code_value(code) for code in reason_code_list],
        )

    def _on_message(self, _client, _userdata, message) -> None:
        try:
            raw_payload = message.payload.decode("utf-8")
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            logger.warning("MQTT payload is not valid JSON. topic=%s", message.topic)
            return

        if not isinstance(payload, dict):
            logger.warning("MQTT payload is not a JSON object. topic=%s payload=%s", message.topic, payload)
            return

        logger.info("MQTT message received. topic=%s payload=%s", message.topic, payload)

        try:
            mapped_payload = mqtt_payload_mapper.parse(payload)
        except ValidationError:
            logger.exception("MQTT payload validation failed. payload=%s", payload)
            return

        if mapped_payload is None:
            logger.warning("MQTT payload did not match any supported schema. payload=%s", payload)
            return

        if hasattr(mapped_payload, "stations"):
            dashboard_service.apply_payload(mapped_payload)
            logger.info("Applied dashboard payload from MQTT. stations=%s", len(mapped_payload.stations))
            return

        dashboard_service.apply_realtime_message(mapped_payload)
        logger.info("Applied realtime MQTT payload. device=%s", mapped_payload.device)


mqtt_consumer_service = MqttConsumerService()
