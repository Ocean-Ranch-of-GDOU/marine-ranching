import os
from dataclasses import dataclass
from pathlib import Path


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = "海洋牧场精准投喂监控中心"
    base_dir: Path = Path(__file__).resolve().parents[2]
    templates_dir: Path = base_dir / "templates"
    static_dir: Path = base_dir / "static"
    port: int = int(os.getenv("PORT", "8000"))
    mqtt_broker: str | None = os.getenv("MQTT_BROKER", "k3f39c3d.ala.cn-hangzhou.emqxsl.cn")
    mqtt_port: int = int(os.getenv("MQTT_PORT", "8883"))
    mqtt_topic: str | None = os.getenv("MQTT_TOPIC", "ocean/mqtt/data")
    mqtt_username: str | None = os.getenv("MQTT_USERNAME", "banana")
    mqtt_password: str | None = os.getenv("MQTT_PASSWORD", "ikun1314")
    mqtt_client_id: str | None = os.getenv("MQTT_CLIENT_ID")
    mqtt_keepalive: int = int(os.getenv("MQTT_KEEPALIVE", "60"))
    mqtt_use_tls: bool = _env_flag("MQTT_USE_TLS", True)
    mqtt_tls_insecure: bool = _env_flag("MQTT_TLS_INSECURE", False)

    @property
    def mqtt_enabled(self) -> bool:
        return bool(self.mqtt_broker and self.mqtt_topic)


settings = Settings()
