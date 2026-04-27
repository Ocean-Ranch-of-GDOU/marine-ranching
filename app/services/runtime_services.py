import logging

from app.core.config import settings
from app.services.demo_data_service import demo_data_service
from app.services.mqtt_consumer_service import mqtt_consumer_service


logger = logging.getLogger("uvicorn.error")


class RuntimeServices:
    def start(self) -> None:
        if settings.mqtt_enabled:
            logger.info(
                "Runtime starting in MQTT mode. broker=%s port=%s topic=%s",
                settings.mqtt_broker,
                settings.mqtt_port,
                settings.mqtt_topic,
            )
            mqtt_consumer_service.start()
        else:
            logger.info("Runtime starting in demo-data mode.")
            demo_data_service.start()

    def stop(self) -> None:
        logger.info("Runtime stopping services.")
        demo_data_service.stop()
        mqtt_consumer_service.stop()


runtime_services = RuntimeServices()
