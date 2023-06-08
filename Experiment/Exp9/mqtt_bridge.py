# !/usr/bin/env python3
# coding:utf-8

"""
    风速：>=10m/s，提醒减速；>=25m/s，禁止通行
    降雨量：>=40mm，禁止通行
    降雪量：>6mm，提醒减速
    能见度：<150m，限速80km/h；<100m，限速50km/h；<50m，禁止通行
"""
import base64
import random
import psutil
import signal
import json
import time
import paho.mqtt.client as mqtt

device_name = '{用户自定义}'
broker = "edgex_host"   # mqtt代理服务器地址在/etc/hosts内修改过
port = 1883  # 端口
keepalive = 60  # 与代理通信之间允许的最长时间段(以秒为单位)，默认60
publish_topic = "incoming9"  # 车辆信息发布主题
visibilities = {'less_50': 5, 'less_100': 30, 'less_150': 60, 'normal': 100}
qualified_path = '正常.jpg'
damage_path = '裂缝.jpg'
'''
1：大桥没有裂缝
2：大桥有裂缝
'''
bridge_qualities = {'2': 5, '1': 100}
# 大桥质量与大桥图片之间建立字典映射
bridge_quality_to_image_path = {'1': qualified_path, '2': damage_path}

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
    client.subscribe(topic="command9")


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
            if value == '禁止通行':
                print("\033[1;31m" + value + "\033[0m")
            else:
                print("\033[1;33m" + value + "\033[0m")

    client.publish(topic="response", payload=json.dumps(ret_data), qos=0)


# 获取能见度的等级：低于50m、低于100m、低于150m、正常
# 获取大桥质量
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


# 获取对应大桥图片路径
def get_bridge_image_path():
    bridge_quality = get_degree(bridge_qualities)
    bridge_image_path = bridge_quality_to_image_path.get(bridge_quality)
    return bridge_image_path


def trans_image(bridge_image_path):
    f = open(bridge_image_path, 'rb')
    bridge_image = base64.b64encode(f.read()).decode('utf-8')
    return bridge_image


# 获取降雨量或降雪量
def get_rain_or_snow_content(degree):
    random_num = random.randint(0, 3)
    pattern = 'normal'
    content = 0
    # 获取降雨量
    if random_num == 0:
        pattern = 'rain'
        if degree == 'less_50':
            content = random.randint(40, 100)
        elif degree == 'less_100' or degree == 'less_150':
            content = random.randint(20, 40)
        else:
            content = random.randint(0, 20)
    # 获取降雪量
    elif random_num == 1:
        pattern = 'snow'
        if degree == 'less_50':
            content = random.randint(10, 20)
        elif degree == 'less_100' or degree == 'less_150':
            content = random.randint(6, 10)
        else:
            content = random.randint(0, 6)
    return pattern, str(content) + 'mm'


# 获取风速
def get_wind_speed(degree):
    if degree == 'less_50':
        speed = random.uniform(25, 40)
    elif degree == 'less_100' or degree == 'less_150':
        speed = random.uniform(10, 25)
    else:
        speed = random.uniform(0, 10)
    return str(round(speed, 2))+'m/s'


# 获取能见度
def get_visibility(degree):
    if degree == 'less_50':
        visibility = random.randint(10, 50)
    elif degree == 'less_100':
        visibility = random.randint(50, 100)
    elif degree == 'less_150':
        visibility = random.randint(100, 150)
    else:
        visibility = random.randint(150, 200)
    return str(visibility)+'m'


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
        degree = get_degree(visibilities)
        visibility = get_visibility(degree)
        info['可见度'] = visibility
        pattern, rain_or_snow_content = get_rain_or_snow_content(degree)
        if pattern == 'rain':
            info['降雨量'] = rain_or_snow_content
        elif pattern == 'snow':
            info['降雪量'] = rain_or_snow_content
        wind_speed = get_wind_speed(degree)
        info['风速'] = wind_speed
        for i in range(20):
            bridge_image_path = get_bridge_image_path()
            bridge_image = trans_image(bridge_image_path)
            info['摄像头' + str(i + 1)] = bridge_image
        memory_used = get_memory_used()
        memory_total = get_memory_total()
        network_sent = get_network_sent()
        cpu_usage = get_cpu_usage()
        # base64编码
        info = str(base64.b64encode(str(info).encode('utf-8')), 'utf-8')
        publish_data = {"device_name": device_name, "memory_used": memory_used, "memory_total": memory_total, "cpu_usage": cpu_usage, "network_sent": network_sent, "bridge_information": "{}".format(info)}
        # print("incoming publish:", json.dumps(publish_data))  # dumps()作用是将dict类型的数据转成str
        # 发布到MQTT上
        client.publish(topic=publish_topic, payload=json.dumps(publish_data), qos=0)
        # 每隔1s发布一次信息
        time.sleep(1)
    client.disconnect()
