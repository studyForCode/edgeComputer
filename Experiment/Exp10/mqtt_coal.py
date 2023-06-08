# !/usr/bin/env python3
# coding:utf-8

import base64
import random
import psutil
import signal
import json
import time
import paho.mqtt.client as mqtt

device_name = '{用户自定义}'
broker = "edgex_host"  # mqtt代理服务器地址在/etc/hosts内修改过
port = 1883  # 端口
keepalive = 60  # 与代理通信之间允许的最长时间段(以秒为单位)，默认60
publish_topic = "incoming10"  # 煤矿信息发布主题
methane_degrees = {'abnormal': 1, 'normal': 50}
personal_number_degrees = {'abnormal': 1, 'normal': 50}
pressure_degrees = {'abnormal': 1, 'normal': 50}

# 定义一个信号量用于强制退出时不影响程序的正常运行
stop = False


def handler(a, b):  # 定义一个signal handling
    global stop
    print("Signal Number:", a, "Frame:", b)
    stop = True
    exit()


signal.signal(signal.SIGINT, handler)  # 将handle分配给对应信号


def on_connect(client, userdata, flags, rc):
    # 响应状态码为0表示连接成功
    if rc == 0:
        print("Connected to MQTT Broker!\n")
    else:
        print("Failed to connect, return code %d\n", rc)
    # 如果与broker失去连接后重连，仍然会继续订阅command主题
    client.subscribe(topic="command10")


def on_message(client, userdata, msg):
    print("topic:", msg.topic, "\nmessage:" + str(msg.payload))
    try:
        rcv_data = json.loads(msg.payload.decode('utf-8'))
        print(rcv_data)
    except:
        print("error")
    ret_data = rcv_data
    alert = rcv_data.get('alert')
    alert = str(base64.b64decode(alert), 'utf-8')
    alert = eval(alert)
    print(rcv_data.get('method'))
    print("method:", rcv_data.get("method", None))
    # 处理set请求，set主题是 'alert'
    if rcv_data.get("method", None) == "set":
        warnings = alert.get('alert')
        for key, value in warnings.items():
            print("\033[1;31m" + value + "\033[0m")

    client.publish(topic="response", payload=json.dumps(ret_data), qos=0)


# 获取甲烷浓度、入井人员数量、矿井气压的状况(异常或正常)
def get_degree(degrees):
    total = sum(degrees.values())
    random_num = random.uniform(0, total)
    curr_sum = 0
    degree = None
    keys = degrees.keys()
    for k in keys:
        curr_sum += degrees[k]  # 在遍历中，累加当前权重值
        if random_num <= curr_sum:  # 当随机数<=当前权重和时，返回权重key
            degree = k
            break
    return degree


# 获取甲烷浓度
def get_methane_content():
    methane_degree = get_degree(methane_degrees)
    if methane_degree == 'normal':
        methane_content1 = random.uniform(2000, 5000)
    else:
        methane_content1 = random.uniform(5000, 6000)
    methane_content2 = random.uniform(methane_content1 - 50, methane_content1 + 50)
    return str(round(methane_content1, 2))+'PPM', str(round(methane_content2, 2))+'PPM'


# 获取煤矿井内气压
def get_pressure():
    pressure_degree = get_degree(pressure_degrees)
    if pressure_degree == 'normal':
        pressure = random.randint(98, 101)
    else:
        pressure = random.randint(101, 150)
    return str(pressure)+'kPa'


# 获取入井人员图片路径
def get_personal_image_path():
    index = random.randint(1, 10)
    personal_image_path = '入井'+str(index)+'.jpg'
    return personal_image_path


def trans_image(personal_image_path):
    f = open(personal_image_path, 'rb')
    personal_image = base64.b64encode(f.read()).decode('utf-8')
    return personal_image


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
    client = mqtt.Client()
    # 连接mqtt服务器
    ret = mqtt_connect(client, "admin", "public", broker, port, keepalive)
    print("mqtt_connect:", ret)
    time.sleep(1)
    while not stop:# and ret == 0:
        info = {}
        methane_content1, methane_content2 = get_methane_content()
        pressure = get_pressure()
        info['甲烷传感器1'] = methane_content1
        info['甲烷传感器2'] = methane_content2
        info['矿井气压'] = pressure
        personal_image_path = get_personal_image_path()
        personal_image = trans_image(personal_image_path)
        info['入井图片'] = personal_image
        memory_used = get_memory_used()
        memory_total = get_memory_total()
        network_sent = get_network_sent()
        cpu_usage = get_cpu_usage()
        # base64编码
        info = str(base64.b64encode(str(info).encode('utf-8')), 'utf-8')
        publish_data = {"device_name": device_name, "memory_used": memory_used, "memory_total": memory_total, "cpu_usage": cpu_usage, "network_sent": network_sent, "coalpit_information": "{}".format(info)}
       # print("incoming publish:", json.dumps(publish_data))  # dumps()作用是将dict类型的数据转成str
        # 发布到MQTT上
        client.publish(topic=publish_topic, payload=json.dumps(publish_data), qos=0)
        # 每隔1s发布一次信息
        time.sleep(1)
    client.disconnect()
