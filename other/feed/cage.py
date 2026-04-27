from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from threading import Thread
import time

# ===================== 配置 =====================
PORT = 502
SLAVE_ID = 1
FEED_LEFT_REG = 1    # 饲料余量 主机读
FEED_REG = 16        # 投喂控制 主机写

# 初始化寄存器
store = ModbusSlaveContext(
    hr=ModbusSequentialDataBlock(0, [0]*100)
)
context = ModbusServerContext(slaves=store, single=True)

# 初始值
store.setValues(3, FEED_LEFT_REG, [100])
store.setValues(3, FEED_REG, [0])

# ===================== 功能1：网箱饲料自动变化 =====================
def cage_control():
    while True:
        try:
            feed_left = store.getValues(3, FEED_LEFT_REG, 1)[0]
            feed_ctrl = store.getValues(3, FEED_REG, 1)[0]

            # 投喂状态：0=减少，1=增加
            if feed_ctrl == 0:
                feed_left = max(0, feed_left - 1)
            else:
                feed_left = min(100, feed_left + 2)

            store.setValues(3, FEED_LEFT_REG, [feed_left])
        except:
            pass
        time.sleep(1)

# ===================== 功能2：无人船自动监测 =====================
def boat_monitor():
    while True:
        try:
            feed_left = store.getValues(3, FEED_LEFT_REG, 1)[0]
            print(f"📊 饲料余量: {feed_left}% | 投喂状态: {store.getValues(3, FEED_REG, 1)[0]}")

            # 余量 ≤20% 自动提示
            if feed_left <= 20:
                print("⚠️  饲料不足 → 等待主机下发补料指令（寄存器16=1）")
        except:
            pass
        time.sleep(2)

# ===================== 启动线程 =====================
Thread(target=cage_control, daemon=True).start()
Thread(target=boat_monitor, daemon=True).start()

# ===================== 从机启动 =====================
print("✅ 网箱 + 无人船 整合从机启动成功！")
print(f"IP: 10.240.254.34")
print(f"端口: {PORT}")
print(f"Slave ID: {SLAVE_ID}")
print(f"饲料余量寄存器: 1 (只读)")
print(f"投喂控制寄存器: 16 (可写，1=补料)")

StartTcpServer(context, address=("0.0.0.0", PORT))