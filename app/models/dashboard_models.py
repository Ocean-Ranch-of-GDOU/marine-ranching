from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Position(BaseModel):
    x: float
    y: float


class StationPayload(BaseModel):
    id: str
    name: str | None = None
    mode: str | None = None
    status: str | None = None
    temperature: float | None = None
    oxygen: float | None = None
    salinity: float | None = None
    wind_speed: float | None = None
    light: float | None = None
    flow_speed: float | None = None
    flow_dir: float | None = None
    feeding_level: float | None = None
    remaining_feed: float | None = None
    today_feed_kg: float | None = None
    position: Position | None = None
    color: str | None = None


class AlarmPayload(BaseModel):
    time: str
    originator: str
    type: str
    severity: Literal["low", "medium", "high"] | str
    status: str
    message: str


class DashboardPayload(BaseModel):
    farm_name: str | None = None
    timestamp: str | None = None
    stations: list[StationPayload] = Field(default_factory=list)
    alarms: list[AlarmPayload] = Field(default_factory=list)


class ChartPoint(BaseModel):
    time: str
    values: list[float]


class StationView(BaseModel):
    id: str
    name: str
    status: str
    mode: str
    temperature: float
    oxygen: float
    salinity: float = 0.0
    wind_speed: float = 0.0
    light: float = 0.0
    flow_speed: float = 0.0
    flow_dir: float = 0.0
    feeding_level: float
    remaining_feed: float
    today_feed_kg: float
    position: Position
    color: str
    last_update: str


class MqttStatus(BaseModel):
    enabled: bool
    broker: str
    port: int
    topic: str


class DashboardState(BaseModel):
    farm_name: str
    updated_at: str
    stations: list[StationView]
    temperature_history: list[ChartPoint]
    feeding_history: list[ChartPoint]
    alarms: list[AlarmPayload]
    mqtt: MqttStatus
    example_payload: dict[str, Any]


class UpdateResponse(BaseModel):
    ok: bool
    updated_at: str


class RealtimeMqttMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    device: str
    water_temp: float | None = None
    dissolved_oxygen: float | None = Field(default=None, alias="do")
    salinity: float | None = None
    wind_speed: float | None = None
    light: float | None = None
    flow_speed: float | None = None
    flow_dir: float | None = None
    remain_material: float | None = None
    time: str | None = None
