import random
import threading
import time

from app.core.time_utils import iso_now
from app.models.dashboard_models import DashboardPayload
from app.services.dashboard_service import dashboard_service


class DemoDataService:
    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="demo-data-updater")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(5)
            state = dashboard_service.get_dashboard_state()
            payload = {"timestamp": iso_now(), "stations": [], "alarms": state["alarms"]}

            for station in state["stations"]:
                next_temp = max(15.0, min(32.0, round(station["temperature"] + random.uniform(-0.8, 0.8), 1)))
                next_oxygen = max(4.0, min(10.0, round(station["oxygen"] + random.uniform(-0.3, 0.3), 1)))
                next_level = max(0.0, min(100.0, round(station["feeding_level"] + random.uniform(-10, 11), 1)))

                payload["stations"].append(
                    {
                        "id": station["id"],
                        "name": station["name"],
                        "mode": station["mode"],
                        "status": station["status"],
                        "temperature": next_temp,
                        "oxygen": next_oxygen,
                        "feeding_level": next_level,
                        "remaining_feed": max(0.0, round(station["remaining_feed"] - random.uniform(0.3, 1.1), 1)),
                        "today_feed_kg": round(station["today_feed_kg"] + random.uniform(0.5, 2.3), 1),
                        "position": station["position"],
                        "color": station["color"],
                    }
                )

            low_oxygen = [item for item in payload["stations"] if item["oxygen"] < 5.3]
            payload["alarms"] = []
            if low_oxygen:
                payload["alarms"].append(
                    {
                        "time": iso_now(),
                        "originator": low_oxygen[0]["name"],
                        "type": "低氧告警",
                        "severity": "high",
                        "status": "active",
                        "message": "溶氧低于 5.3 mg/L，请立即排查。",
                    }
                )

            dashboard_service.apply_payload(DashboardPayload.model_validate(payload))


demo_data_service = DemoDataService()
