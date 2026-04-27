from pymodbus.client import ModbusTcpClient
import time

CAGE_IP = "127.0.0.1"
CAGE_PORT = 502

def check_feed():
    while True:
        try:
            client = ModbusTcpClient(CAGE_IP, CAGE_PORT)
            client.connect()
            res = client.read_holding_registers(1, 1, slave=1)
            client.close()

            if not res.isError():
                val = res.registers[0]
                print(f"📊 饲料余量: {val}%")
                if val <= 20:
                    print("⚠️ 饲料不足，等待主机补料")
        except:
            pass
        time.sleep(2)

check_feed()