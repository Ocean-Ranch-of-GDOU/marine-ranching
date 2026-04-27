from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import time
import json
import paho.mqtt.client as mqtt
import ssl
from typing import Optional, Dict, Any

# ==============================================
# 🔧 配置区（仅需修改这里）
# ==============================================
# 从机配置：从机1=环境监测，从机2=投喂控制
SLAVES = {
    "slave1": {"ip": "10.240.254.92", "id": 1, "name": "一号牧场环境"},
    "slave2": {"ip": "10.240.254.34", "id": 2, "name": "一号牧场投喂"}
}

# 从机1 寄存器配置（环境监测）
SLAVE1_REGS = {
    "temp": 100,      # 水温
    "do": 2,        # 溶解氧
    "salinity": 3,  # 盐度
    "wind": 4,      # 风速
    "light": 5,     # 光照(双寄存器)
    "read_count": 8 # 读取寄存器数量
}

# 从机2 寄存器配置（投喂控制）
SLAVE2_REGS = {
    "remain": 1,      # 余料
    "feed_ctrl": 16,  # 投喂控制寄存器
    "read_count": 1   # 读取寄存器数量
}

# MQTT配置
MQTT_CONFIG = {
    "broker": "k3f39c3d.ala.cn-hangzhou.emqxsl.cn",
    "port": 8883,
    "user": "banana",
    "pwd": "ikun1314",
    "topic": "ocean/mqtt/data",
    "keepalive": 60
}

# 业务阈值 ✅ 仅保留：余料低于30触发投喂
AUTO_FEED_REMAIN = 30    # 余料低于该值自动投喂
FEED_DELAY = 10          # 投喂持续时间(秒)
LOOP_DELAY = 3           # 主循环间隔(秒)

# ==============================================
# 🛠️ 通用工具函数（Modbus/MQTT封装，无重复代码）
# ==============================================
def modbus_client_connect(ip: str, slave_id: int) -> Optional[ModbusTcpClient]:
    """创建并连接Modbus TCP客户端"""
    try:
        client = ModbusTcpClient(host=ip, port=502, timeout=2)
        client.unit_id = slave_id
        if client.connect():
            return client
        client.close()
        return None
    except Exception as e:
        print(f"Modbus连接失败: {str(e)}")
        return None

def modbus_read_registers(client: ModbusTcpClient, addr: int, count: int) -> Optional[list]:
    """通用读保持寄存器"""
    try:
        result = client.read_holding_registers(address=addr, count=count)
        return result.registers if not result.isError() else None
    except ModbusException:
        return None

def modbus_write_single_register(client: ModbusTcpClient, addr: int, value: int) -> bool:
    """通用写单寄存器"""
    try:
        result = client.write_register(address=addr, value=value)
        return not result.isError()
    except ModbusException:
        return False

# ==============================================
# 📡 MQTT客户端初始化
# ==============================================
def on_connect(client: mqtt.Client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ MQTT 连接成功")
    else:
        print(f"❌ MQTT 连接失败，错误码: {rc}")

def init_mqtt_client() -> mqtt.Client:
    """初始化MQTT客户端（支持SSL）"""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.username_pw_set(MQTT_CONFIG["user"], MQTT_CONFIG["pwd"])
    # SSL配置（兼容云服务器）
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)
    # 连接服务器
    client.connect(
        MQTT_CONFIG["broker"],
        MQTT_CONFIG["port"],
        MQTT_CONFIG["keepalive"]
    )
    client.loop_start()
    time.sleep(1)
    return client

# 全局MQTT客户端
mqtt_client = init_mqtt_client()

# ==============================================
# 📊 从机数据读取（独立解析，互不干扰）
# ==============================================
def read_environment_data() -> Optional[Dict[str, Any]]:
    """读取从机1：环境监测数据"""
    slave = SLAVES["slave1"]
    client = modbus_client_connect(slave["ip"], slave["id"])
    if not client:
        return None

    regs = modbus_read_registers(client, SLAVE1_REGS["temp"], SLAVE1_REGS["read_count"])
    client.close()

    if not regs:
        return None

    # 数据解析（按协议转换）
    return {
        "device": slave["name"],
        "water_temp": round(regs[0] / 100.0, 2),
        "do": round(regs[1] / 100.0, 2),
        "salinity": round(regs[2] / 10.0, 2),
        "wind_speed": round(regs[3] / 100.0, 2),
        "light": regs[4] * 65536 + regs[5],
        "flow_speed": round(regs[6] / 100.0, 2),
        "flow_dir": round(regs[7],2),
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def read_feed_data() -> Optional[Dict[str, Any]]:
    """读取从机2：投喂设备数据（余料）"""
    slave = SLAVES["slave2"]
    client = modbus_client_connect(slave["ip"], slave["id"])
    if not client:
        return None

    regs = modbus_read_registers(client, SLAVE2_REGS["remain"], SLAVE2_REGS["read_count"])
    client.close()

    if not regs:
        return None

    return {
        "device": slave["name"],
        "remain_material": regs[0],  # 余料
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# ==============================================
# 🎛️ 投喂控制（仅发送给从机2）
# ==============================================
def auto_feed_control() -> None:
    """执行自动投喂：仅控制从机2"""
    slave = SLAVES["slave2"]
    client = modbus_client_connect(slave["ip"], slave["id"])
    if not client:
        print("❌ 投喂失败：无法连接从机2")
        return

    print("▶ 开始投喂：写入寄存器 1")
    modbus_write_single_register(client, SLAVE2_REGS["feed_ctrl"], 1)
    time.sleep(FEED_DELAY)

    print("▶ 结束投喂：写入寄存器 0")
    modbus_write_single_register(client, SLAVE2_REGS["feed_ctrl"], 0)
    client.close()
    print("✅ 从机2 投喂完成\n")

# ==============================================
# 🚀 主程序循环
# ==============================================
def main():
    print("🌊 海洋牧场监控系统已启动（优化稳定版）")

    while True:
        # 1. 读取从机1环境数据
        env_data = read_environment_data()
        if env_data:
            print("📥 从机1数据:", env_data)
            mqtt_client.publish(MQTT_CONFIG["topic"], json.dumps(env_data, ensure_ascii=False))

        # 2. 读取从机2投喂数据
        feed_data = read_feed_data()
        if feed_data:
            print("📥 从机2数据:", feed_data)
            mqtt_client.publish(MQTT_CONFIG["topic"], json.dumps(feed_data, ensure_ascii=False))

        # 3. ✅ 仅保留：余料低于30 自动投喂
        if feed_data and feed_data["remain_material"] < AUTO_FEED_REMAIN:
            print("🔥 余料不足，启动自动投喂...")
            auto_feed_control()

        # 循环间隔
        time.sleep(LOOP_DELAY)

if __name__ == "__main__":
    main()