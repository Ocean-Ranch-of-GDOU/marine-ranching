import random
import re
import threading
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any

from app.core.config import settings
from app.core.time_utils import chart_time_label, iso_now
from app.models.dashboard_models import DashboardPayload, RealtimeMqttMessage


class DashboardRepository:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = self._build_demo_state()

    def _build_demo_state(self) -> dict[str, Any]:
        names = ["1号投喂区", "2号投喂区", "3号投喂区"]
        colors = ["#ff5b57", "#27ae60", "#2d7ff9"]
        points = [{"x": 26, "y": 34}, {"x": 48, "y": 25}, {"x": 65, "y": 43}]
        temperature_history: list[dict[str, Any]] = []
        feeding_history: list[dict[str, Any]] = []
        now = datetime.now()

        for idx in range(30):
            stamp = (now - timedelta(minutes=29 - idx)).strftime("%H:%M")
            temperature_history.append(
                {
                    "time": stamp,
                    "values": [
                        round(22 + random.uniform(-1.8, 1.6), 1),
                        round(20 + random.uniform(-1.2, 1.1), 1),
                        round(23.5 + random.uniform(-2.0, 2.2), 1),
                    ],
                }
            )
            feeding_history.append(
                {
                    "time": stamp,
                    "values": [
                        round(45 + random.uniform(-14, 25), 1),
                        round(32 + random.uniform(-10, 33), 1),
                        round(55 + random.uniform(-18, 21), 1),
                    ],
                }
            )

        stations = []
        for idx, name in enumerate(names):
            stations.append(
                {
                    "id": f"zone-{idx + 1}",
                    "name": name,
                    "status": "online",
                    "mode": "自动投喂",
                    "temperature": temperature_history[-1]["values"][idx],
                    "oxygen": round(6.8 + random.uniform(-0.5, 0.8), 1),
                    "salinity": round(27 + random.uniform(-1.4, 1.7), 1),
                    "wind_speed": round(1.5 + random.uniform(0.2, 1.9), 1),
                    "light": round(28000 + random.uniform(-6000, 9000), 1),
                    "flow_speed": round(0.35 + random.uniform(-0.08, 0.12), 2),
                    "flow_dir": round(125 + random.uniform(-35, 42), 1),
                    "feeding_level": feeding_history[-1]["values"][idx],
                    "remaining_feed": round(65 + random.uniform(-18, 20), 1),
                    "today_feed_kg": round(120 + random.uniform(-30, 45), 1),
                    "position": points[idx],
                    "color": colors[idx],
                    "last_update": iso_now(),
                }
            )

        return {
            "farm_name": settings.app_name,
            "updated_at": iso_now(),
            "stations": stations,
            "temperature_history": temperature_history,
            "feeding_history": feeding_history,
            "alarms": [],
            "mqtt": {
                "enabled": False,
                "broker": settings.mqtt_broker or "127.0.0.1",
                "port": settings.mqtt_port,
                "topic": settings.mqtt_topic or "ocean/farm/feeding",
            },
            "example_payload": {
                "farm_name": settings.app_name,
                "timestamp": iso_now(),
                "stations": [
                    {
                        "id": "zone-1",
                        "name": "1号投喂区",
                        "mode": "自动投喂",
                        "status": "online",
                        "temperature": 22.8,
                        "oxygen": 7.1,
                        "salinity": 28.6,
                        "wind_speed": 2.1,
                        "light": 34500,
                        "flow_speed": 0.42,
                        "flow_dir": 138.0,
                        "feeding_level": 68.5,
                        "remaining_feed": 71.2,
                        "today_feed_kg": 138.0,
                        "position": {"x": 26, "y": 34},
                    }
                ],
                "alarms": [
                    {
                        "time": iso_now(),
                        "originator": "2号投喂区",
                        "type": "低氧告警",
                        "severity": "high",
                        "status": "active",
                        "message": "溶氧低于阈值，请检查增氧设备。",
                    }
                ],
            },
        }

    def get_state(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._state)

    def get_example_payload(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._state["example_payload"])

    def set_mqtt_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._state["mqtt"]["enabled"] = enabled

    def _build_station_defaults(
        self,
        station_id: str,
        name: str,
        current_time: str,
        index: int | None = None,
    ) -> dict[str, Any]:
        colors = ["#ff5b57", "#27ae60", "#2d7ff9", "#00b8d9", "#ff9f1a"]
        points = [
            {"x": 26, "y": 34},
            {"x": 48, "y": 25},
            {"x": 65, "y": 43},
            {"x": 37, "y": 54},
            {"x": 58, "y": 58},
        ]
        resolved_index = index if index is not None else len(self._state["stations"])
        return {
            "id": station_id,
            "name": name,
            "status": "online",
            "mode": "自动投喂",
            "temperature": 0.0,
            "oxygen": 0.0,
            "salinity": 0.0,
            "wind_speed": 0.0,
            "light": 0.0,
            "flow_speed": 0.0,
            "flow_dir": 0.0,
            "feeding_level": 0.0,
            "remaining_feed": 0.0,
            "today_feed_kg": 0.0,
            "position": points[resolved_index % len(points)],
            "color": colors[resolved_index % len(colors)],
            "last_update": current_time,
        }

    def _append_history_snapshot(self) -> None:
        self._state["temperature_history"].append(
            {
                "time": chart_time_label(include_seconds=True),
                "values": [item["temperature"] for item in self._state["stations"]],
            }
        )
        self._state["feeding_history"].append(
            {
                "time": chart_time_label(include_seconds=True),
                "values": [item["feeding_level"] for item in self._state["stations"]],
            }
        )
        self._state["temperature_history"] = self._state["temperature_history"][-30:]
        self._state["feeding_history"] = self._state["feeding_history"][-30:]

    def _resolve_station_by_device(self, device: str) -> dict[str, Any] | None:
        normalized_device = device.strip().lower()
        stations = self._state["stations"]

        for station in stations:
            if station["name"].strip().lower() == normalized_device:
                return station
            if station["id"].strip().lower() == normalized_device:
                return station

        number_match = re.search(r"(\d+)", device)
        if number_match:
            station_index = int(number_match.group(1)) - 1
            if 0 <= station_index < len(stations):
                return stations[station_index]

        return None

    def _infer_feeding_level(self, remaining_feed: float) -> float:
        return round(max(0.0, min(100.0, 100.0 - remaining_feed)), 1)

    def update_from_payload(self, payload: DashboardPayload) -> dict[str, Any]:
        with self._lock:
            payload_data = payload.model_dump(mode="python", exclude_none=True)

            if payload_data.get("farm_name"):
                self._state["farm_name"] = payload_data["farm_name"]

            stations_by_id = {item["id"]: item for item in self._state["stations"]}
            current_time = payload_data.get("timestamp", iso_now())

            for incoming in payload_data.get("stations", []):
                station_id = incoming["id"]
                station = stations_by_id.get(station_id)

                if station is None:
                    station = self._build_station_defaults(
                        station_id=station_id,
                        name=incoming.get("name", station_id),
                        current_time=current_time,
                    )
                    station["position"] = incoming.get("position", station["position"])
                    station["color"] = incoming.get("color", station["color"])
                    self._state["stations"].append(station)
                    stations_by_id[station_id] = station

                station.update(
                    {
                        "name": incoming.get("name", station["name"]),
                        "status": incoming.get("status", station["status"]),
                        "mode": incoming.get("mode", station["mode"]),
                        "temperature": incoming.get("temperature", station["temperature"]),
                        "oxygen": incoming.get("oxygen", station["oxygen"]),
                        "salinity": incoming.get("salinity", station["salinity"]),
                        "wind_speed": incoming.get("wind_speed", station["wind_speed"]),
                        "light": incoming.get("light", station["light"]),
                        "flow_speed": incoming.get("flow_speed", station["flow_speed"]),
                        "flow_dir": incoming.get("flow_dir", station["flow_dir"]),
                        "feeding_level": incoming.get("feeding_level", station["feeding_level"]),
                        "remaining_feed": incoming.get("remaining_feed", station["remaining_feed"]),
                        "today_feed_kg": incoming.get("today_feed_kg", station["today_feed_kg"]),
                        "position": incoming.get("position", station["position"]),
                        "color": incoming.get("color", station["color"]),
                        "last_update": current_time,
                    }
                )

            if payload_data.get("stations"):
                self._append_history_snapshot()

            if "alarms" in payload_data:
                self._state["alarms"] = payload_data["alarms"][-20:]

            self._state["updated_at"] = current_time
            return deepcopy(self._state)

    def update_from_realtime_message(self, message: RealtimeMqttMessage) -> dict[str, Any]:
        with self._lock:
            current_time = message.time or iso_now()
            station = self._resolve_station_by_device(message.device)

            if station is None:
                station_id = f"zone-{len(self._state['stations']) + 1}"
                station = self._build_station_defaults(
                    station_id=station_id,
                    name=message.device,
                    current_time=current_time,
                )
                self._state["stations"].append(station)

            station["status"] = "online"
            station["mode"] = "自动投喂"
            station["last_update"] = current_time

            if message.water_temp is not None:
                station["temperature"] = round(message.water_temp, 2)
            if message.dissolved_oxygen is not None:
                station["oxygen"] = round(message.dissolved_oxygen, 2)
            if message.salinity is not None:
                station["salinity"] = round(message.salinity, 2)
            if message.wind_speed is not None:
                station["wind_speed"] = round(message.wind_speed, 2)
            if message.light is not None:
                station["light"] = round(message.light, 2)
            if message.flow_speed is not None:
                station["flow_speed"] = round(message.flow_speed, 2)
            if message.flow_dir is not None:
                station["flow_dir"] = round(message.flow_dir, 2)
            if message.remain_material is not None:
                station["remaining_feed"] = round(message.remain_material, 2)
                station["feeding_level"] = self._infer_feeding_level(message.remain_material)

            self._append_history_snapshot()
            self._state["updated_at"] = current_time
            return deepcopy(self._state)


dashboard_repository = DashboardRepository()
