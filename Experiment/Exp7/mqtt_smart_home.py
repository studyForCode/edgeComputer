# !/usr/bin/env python3
# coding:utf-8

# 导入需要用到的模块
import base64
import psutil
import signal
import json
import time
import smbus
import paho.mqtt.client as mqtt
from picamera import PiCamera
import RPi.GPIO as GPIO

device_name = 'smarthome23'
broker = "edgex_host"  # mqtt代理服务器地址在/etc/hosts内修改过
port = 1883  # 端口
keepalive = 60  # 与代理通信之间允许的最长时间段(以秒为单位)，默认60
publish_topic = "incoming7"  
btn_pin = 11  # 轻触按键Pin口
AC_temp = 0
# 通过按键控制模式转变
mode = 'out_home'  # 初始模式是主人外出默认


camera = PiCamera()
image_path = 'image.jpg'

# 定义一个信号量用于强制退出时不影响程序的正常运行
stop = False


def handler(a, b):   # 定义一个signal handling
    global stop
    print("Signal Number:", a, "Frame:", b)
    stop = True
    exit()


signal.signal(signal.SIGINT, handler)   # 将handle分配给对应信号


def on_connect(client, userdata, flags, rc):
    # 响应状态码为0表示连接成功
    if rc == 0:
        print("Connected to MQTT Broker!\n")
    else:
        print("Failed to connect, return code %d\n", rc)
    # 如果与broker失去连接后重连，仍然会继续订阅ACStatus主题
    client.subscribe(topic="command7")


def on_message(client, userdata, msg):
    global AC_temp
    print("topic:", msg.topic, "\nmessage:" + str(msg.payload))
    try:
        rcv_data = json.loads(msg.payload.decode('utf-8'))
    except:
        print("error")
    ret_data = rcv_data
    print("method:", rcv_data.get("method", None))
    # 处理set请求
    if rcv_data.get("method", None) == "set":
        cmd = int(rcv_data.get("ACStatus", 0))
        print("cmd:", rcv_data.get("cmd", None))
        print("set resource value:", cmd)
        # 收到的消息为"0"，关闭空调
        if cmd == 0:
            AC_temp = 0
        # 收到的消息为"1"，打开空调
        elif cmd == 1:
            AC_temp = 27

    client.publish(topic="response", payload=json.dumps(ret_data), qos=0)


def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    # 设置btn_pin为输入模式，上拉至高电平(3.3V)
    GPIO.setup(btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # 中断函数，当轻触按键按下时，调用detect函数
    GPIO.add_event_detect(btn_pin, GPIO.BOTH, callback=detect, bouncetime=200)


def change_mode(x):
    global mode
    if x == 0:
        if mode == 'out_home':
            mode = 'in_home'
        else:
            mode = 'out_home'


def detect(chn):
    change_mode(GPIO.input(btn_pin))


# 照相函数
def get_image():
    camera.resolution = (1024, 768)  # 摄像界面为1024*768
    camera.start_preview()  # 开始摄像
    camera.capture(image_path)  # 拍照并保存
    camera.stop_preview()


class MLX90614:
    MLX90614_TA = 0X06  # 获取环境温度
    MLX90614_TOBJ1 = 0X07  # 获取物体温度

    comm_retries = 5
    comm_sleep_amount = 0.1

    def __init__(self, address=0x5a, bus_num=1):
        self.bus_num = bus_num
        self.address = address
        self.bus = smbus.SMBus(bus=bus_num)

    def read_reg(self, reg_addr):
        err = None
        for i in range(self.comm_retries):
            try:
                return self.bus.read_word_data(self.address, reg_addr)
            except IOError as e:
                err = e
                # 速率限制-睡眠以防止传感器在请求数据太快时出现问题
                time.sleep(self.comm_sleep_amount)
        raise err

    def data_to_temp(self, data):
        temp = (data * 0.02) - 273.15
        return temp

    def get_amb_temp(self):
        data = self.read_reg(self.MLX90614_TA)
        return self.data_to_temp(data)


def trans_image(image_path):
    fp = open(image_path, 'rb')
    image = base64.b64encode(fp.read()).decode('utf-8')
    return image


# 获取终端内存已使用空间(MB)
def get_memory_used():
    return int(psutil.virtual_memory().used / (1024 * 1024))


# 获取终端内存总空间(MB)
def get_memory_total():
    return int(psutil.virtual_memory().total / (1024 * 1024))


# 获取终端网络发送字节数(MB)
def get_network_sent():
    return int(psutil.net_io_counters().bytes_sent / (1024 * 1024))


'''
CPU使用率，每秒刷新一次
interval:指定的是计算cpu使用率的时间间隔，interval不为0时,则阻塞时显示interval执行的时间内的平均利用率
'''
def get_cpu_usage():
    return str(psutil.cpu_percent(interval=1)) + '%'


def mqtt_connect(client, username, password, broker_ip, broker_port, keepalive):
    ret = 0
    try:
        client.on_connect = on_connect
        client.on_message = on_message
        client.username_pw_set(username, password)
        ret = client.connect(broker_ip, broker_port, keepalive)
        client.loop_start()
    except:
        ret = -1
    return ret


if __name__ == "__main__":
    setup()
    client = mqtt.Client()
    # 连接mqtt服务器
    ret = mqtt_connect(client, "admin", "public", broker, port, keepalive)
    time.sleep(1)
    print("mqtt_connect:", ret)
    while not stop:
        if mode == 'out_home':
            get_image()
            image = trans_image(image_path)
            image_time = time.strftime('%Y-%m-%d %H:%M:%S')
            memory_used = get_memory_used()
            memory_total = get_memory_total()
            network_sent = get_network_sent()
            cpu_usage = get_cpu_usage()
            publish_data = {'device_name': device_name, 'memory_used': memory_used, 'memory_total': memory_total, 'network_sent': network_sent, 'cpu_usage': cpu_usage, 'mode': mode, 'image_time': image_time, 'image': '{}'.format(image)}
            print("incoming publish:", json.dumps(publish_data))  # dumps()作用是将dict类型的数据转成str
            # 发布到MQTT上
            client.publish(topic=publish_topic, payload=json.dumps(publish_data), qos=0)
            # 每隔1s发布一次信息
            time.sleep(1)
        else:
            sensor = MLX90614()
            surrounding_temp = sensor.get_amb_temp()
            memory_used = get_memory_used()
            memory_total = get_memory_total()
            network_sent = get_network_sent()
            cpu_usage = get_cpu_usage()
            publish_data = {'device_name': device_name, 'memory_used': memory_used, 'memory_total': memory_total, 'network_sent': network_sent, 'cpu_usage': cpu_usage, 'mode': mode, 'surrounding_temp': '{:.1f}'.format(surrounding_temp), 'AC_temp': AC_temp}
            print("incoming publish:", json.dumps(publish_data))  # dumps()作用是将dict类型的数据转成str
            # 发布到MQTT上
            client.publish(topic=publish_topic, payload=json.dumps(publish_data), qos=0)
            time.sleep(1)
    client.disconnect()
