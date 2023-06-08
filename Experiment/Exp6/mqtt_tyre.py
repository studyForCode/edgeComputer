# !/usr/bin/env python3
# coding:utf-8

# 导入需要用到的模块
import base64
import random
import psutil
import signal
import json
import time
import paho.mqtt.client as mqtt

device_name = 'tyre23'
broker = "edgex_host"  # mqtt代理服务器地址在/etc/hosts内修改过
port = 1883  # 端口
keepalive = 60  # 与代理通信之间允许的最长时间段(以秒为单位)，默认60
publish_topic = "incoming6"  # 零件信息发布主题
qualified_path = '合格.jpg'
indentation_path = '压痕.jpg'
damage_path = '破损.jpg'
penetration_path = '贯穿破坏.jpg'
'''
1：轮胎合格
2：轮胎压痕
3：轮胎破损
4：轮胎贯穿破坏
'''
tire_qualities = {'4': 1, '2': 5, '3': 5, '1': 100}
# 轮胎质量与轮胎图片之间建立字典映射
tire_quality_to_image_path = {'1': qualified_path, '2': indentation_path, '3': damage_path, '4': penetration_path}

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


# 获取轮胎质量
def get_tire_quality():
    total = sum(tire_qualities.values())
    random_num = random.uniform(0, total)
    curr_sum = 0
    tire_quality = None
    keys = tire_qualities.keys()
    for k in keys:
        curr_sum += tire_qualities[k]  # 在遍历中，累加当前权重值
        if random_num <= curr_sum:  # 当随机数<=当前权重和时，返回权重key
            tire_quality = k
            break
    return tire_quality


# 获取对应轮胎图片路径
def get_tire_image_path():
    tire_quality = get_tire_quality()
    tire_image_path = tire_quality_to_image_path.get(tire_quality)
    print(tire_quality)
    return tire_image_path


def trans_image(tire_image_path):
    f = open(tire_image_path, 'rb')
    tire_image = base64.b64encode(f.read()).decode('utf-8')
    return tire_image


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
    time.sleep(1)
    # print("mqtt_connect:", ret)
    tire_id = 0
    while not stop:# and ret == 0:
        tire_image_path = get_tire_image_path()
        tire_image = trans_image(tire_image_path)
        tire_id += 1
        memory_used = get_memory_used()
        memory_total = get_memory_total()
        network_sent = get_network_sent()
        cpu_usage = get_cpu_usage()
        publish_data = {'device_name': device_name, 'memory_used': memory_used, 'memory_total': memory_total, 'network_sent': network_sent, 'cpu_usage': cpu_usage, 'tire_id': tire_id, 'timestamp': int(time.time()), 'tire_image': '{}'.format(tire_image)}
       # print("incoming publish:", json.dumps(publish_data))  # dumps()作用是将dict类型的数据转成str
        # 发布到MQTT上
        client.publish(topic=publish_topic, payload=json.dumps(publish_data), qos=0)
        # 每隔1s发布一次信息
        time.sleep(3)
    client.disconnect()
