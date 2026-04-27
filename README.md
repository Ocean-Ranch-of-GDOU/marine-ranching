# marine_ranching

基于 FastAPI 与 MQTT 的海洋牧场精准投喂可视化监控平台。

本项目面向海洋牧场场景，围绕投喂设备、环境传感器和视频监控数据，提供单屏大屏展示、实时状态监测、趋势分析和监控弹窗交互能力。后端采用模块化 FastAPI 架构，前端采用原生 HTML、CSS、JavaScript 构建可视化界面，并支持通过 MQTT 接入真实设备数据。

## Features

- 海洋牧场投喂区总览与设备点位展示
- 投喂区状态表格实时更新
- 水温趋势与投喂进度趋势图可视化
- 告警中心展示最近告警信息
- 实时监控弹窗交互界面
- 支持 MQTT 实时接入真实传感器与余料数据
- 支持模拟数据模式，便于本地开发和界面联调

## Tech Stack

- Python 3.12+
- FastAPI
- Uvicorn
- Paho MQTT
- HTML / CSS / JavaScript

## Project Structure

```text
marine_ranching/
├── app/
│   ├── api/routes/                 # 页面与数据接口
│   ├── core/                       # 配置与时间工具
│   ├── models/                     # Pydantic 数据模型
│   ├── repositories/               # 状态仓储与数据合并
│   └── services/                   # MQTT、模拟数据、运行期服务
├── static/                         # 前端静态资源
├── templates/                      # 页面模板
├── main.py                         # 启动入口
├── requirements.txt
└── README.md
```

## Main Pages And APIs

- `/`
  海洋牧场精准投喂监控大屏首页

- `/api/dashboard`
  返回当前前端展示所需的完整大屏数据

- `/api/example-payload`
  返回示例 dashboard payload 结构

- `/api/payload`
  接收标准 dashboard JSON 数据并更新页面状态

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the project

```bash
python main.py
```

启动后访问：

```text
http://127.0.0.1:8000
```

## MQTT Real-Time Data Access

项目已支持通过 MQTT 接入真实数据，并自动将消息合并到前端当前展示状态。

### Supported MQTT data types

1. 环境传感器数据

```json
{
  "device": "1号投喂区",
  "water_temp": 23.41,
  "do": 7.26,
  "salinity": 28.5,
  "wind_speed": 1.42,
  "light": 32560,
  "flow_speed": 0.38,
  "flow_dir": 126,
  "time": "2026-04-27 10:30:00"
}
```

2. 余料数据

```json
{
  "device": "1号投喂区",
  "remain_material": 42,
  "time": "2026-04-27 10:30:00"
}
```

### Default MQTT configuration

当前项目默认读取以下 MQTT 配置，也支持通过环境变量覆盖：

```text
MQTT_BROKER=k3f39c3d.ala.cn-hangzhou.emqxsl.cn
MQTT_PORT=8883
MQTT_TOPIC=ocean/mqtt/data
MQTT_USERNAME=banana
MQTT_PASSWORD=ikun1314
MQTT_KEEPALIVE=60
MQTT_USE_TLS=true
MQTT_TLS_INSECURE=false
```

### Run with custom environment variables

```bash
MQTT_BROKER=your-broker \
MQTT_PORT=8883 \
MQTT_TOPIC=your/topic \
MQTT_USERNAME=your-username \
MQTT_PASSWORD=your-password \
python main.py
```

## Data Flow

```text
Sensor / feeder device
        ↓
     MQTT broker
        ↓
FastAPI MQTT consumer
        ↓
Dashboard repository merge
        ↓
/api/dashboard
        ↓
Frontend polling refresh
```

## Frontend Display Modules

- 牧场点位总览
- 投喂区状态表格
- 水温趋势图
- 投喂进度图
- 告警中心
- 实时监控弹窗

## Notes

- 如果未安装 `paho-mqtt`，项目会无法接入真实 MQTT 数据。
- 如果 MQTT 未成功连接，页面仍可在模拟数据模式下运行。
- 建议在生产环境中通过环境变量管理 MQTT 账号、密码和地址，不要直接写入代码仓库。

## Future Improvements

- 接入真实视频流，如 RTSP/HLS
- 增加投喂参数表单提交接口
- 增加设备在线离线状态检测
- 增加告警规则与告警推送能力
- 增加用户权限和设备管理模块

## License

This project currently does not specify an open-source license.
