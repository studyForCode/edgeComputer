# !/usr/bin/env python3
# coding:utf-8

# 导入需要用到的模块
import json
import signal
import paho.mqtt.client as mqtt
import smbus
import time
import base64
from picamera import PiCamera

device_name = '{用户自定义}'

broker = "edgex_host"  # mqtt代理服务器地址在/etc/hosts内修改过
port = 1883  # 端口
keepalive = 60  # 与代理通信之间允许的最长时间段(以秒为单位)，默认60
subscribe_topic = "command4"   # 121订阅主题
publish_topic_img = "incoming4"   # 图片发布主题

camera = PiCamera()

# 定义一个信号量用于强制退出时不影响程序的正常运行
stop = False


def handler(a, b):   # 定义一个signal handling
    global stop
    print("Signal Number:", a, "Frame:", b)
    stop = True
    camera.close()
    exit()


signal.signal(signal.SIGINT, handler)   # 将handle分配给对应信号


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

    def get_obj_temp(self):
        data = self.read_reg(self.MLX90614_TOBJ1)
        return self.data_to_temp(data)


def on_connect(client, userdata, flags, rc):
    # 响应状态码为0表示连接成功
    if rc == 0:
        print("Connected to MQTT Broker!\n")
    else:
        print("Failed to connect, return code %d\n", rc)
    # 如果与broker失去连接后重连，仍然会继续订阅ledStatus主题
    client.subscribe(topic=subscribe_topic)


sensor = MLX90614()
temperature = float(sensor.get_amb_temp())  # 设置初始温度为环境温度


def on_message(client, userdata, msg):
    global temperature
    print("topic:", msg.topic, "\nmessage:" + str(msg.payload))
    try:
        rcv_data = json.loads(msg.payload.decode('utf-8'))
    except:
        print("error")
    ret_data = rcv_data
    print("method:", rcv_data.get("method", None))
    # 处理get请求
    if rcv_data.get("method", None) == "get":
        print("cmd:", rcv_data.get("cmd", None))
        if rcv_data.get("cmd", None) == "temp":
            # 上报温度到mqtt
            temperature = int(sensor.get_obj_temp())  # 获取人体温度
            ret_data["temp"] = "{}".format(temperature)
            print("response publish:", json.dumps(ret_data))
            client.publish(topic="response", payload=json.dumps(ret_data), qos=0)
            temperature = float(sensor.get_amb_temp())  # 将温度重置为环境温度


# 照相函数
def get_image():
    camera.resolution = (1024, 768)  # 摄像界面为1024*768
    camera.start_preview()  # 开始摄像
    camera.capture('faceimage.jpg')  # 拍照并保存
    camera.stop_preview()


# 对图片的格式进行转换
def trans_image():
    f = open('faceimage.jpg', 'rb')
    img = base64.b64encode(f.read()).decode('utf-8')
    return img


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
    client = mqtt.Client()
    # 连接mqtt服务器
    ret = mqtt_connect(client, "admin", "public", broker, port, keepalive)
    print("mqtt_connect:", ret)
    time.sleep(1)
    while not stop:#ret==0 and not stop:
        # 拍摄照片
        get_image()
        # 将照片格式转换为base64编码
        img = trans_image()
        # 上报照片到mqtt
        publish_data = {"device_name": device_name, "image": "{}".format(img)}
        # print("incoming publish:", json.dumps(publish_data))  # dumps()作用是将dict类型的数据转成str
        # 发布到MQTT上
        client.publish(topic=publish_topic_img, payload=json.dumps(publish_data), qos=0)
        time.sleep(3)
    client.disconnect()
