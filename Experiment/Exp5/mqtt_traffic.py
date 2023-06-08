# !/usr/bin/env python3
# coding:utf-8

# 导入需要用到的模块
import base64
import random
import string
import psutil
import signal
import json
import time
import paho.mqtt.client as mqtt

device_name = 'traffic23'
broker = "edgex_host"  # mqtt代理服务器地址在/etc/hosts内修改过
port = 1883  # 端口
keepalive = 60  # 与代理通信之间允许的最长时间段(以秒为单位)，默认60
publish_topic = "incoming5"  # 车辆信息发布主题
colors = ['红色', '绿色', '黄色', '蓝色', '橙色', '青色', '紫色', '灰色',
          '粉色', '白色', '棕色']
car_brands = ['本田', '丰田', '三菱', '铃木', '马自达', '奔驰', '宝马', '大众',
              '雪佛兰', '福特', '比亚迪', '奇瑞', '吉利', '红旗']
provinces = {'渝': 1, '蒙': 2, '甘': 3, '川': 3, '鄂': 5, '豫': 6, '晋': 6, '京': 10, '陕': 100}

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


# 获取汽车品牌信息
def get_car_brand():
    return random.choice(car_brands)


# 获取汽车车身颜色信息
def get_color():
    return random.choice(colors)


# 生成车牌的省份简称，其中‘陕’权重值最大
def get_license_plate_province():
    total = sum(provinces.values())
    random_num = random.uniform(0, total)
    curr_sum = 0
    province = None
    keys = provinces.keys()
    for k in keys:
        curr_sum += provinces[k]  # 在遍历中，累加当前权重值
        if random_num <= curr_sum:  # 当随机数<=当前权重和时，返回权重key
            province = k
            break
    return province


# 获取车牌
def get_license_plate():
    license_plate_tail = ""
    letter_num = 0
    for i in range(5):
        # 后五位车牌最多包含两个字母
        if letter_num < 2:
            random_num = random.randint(0, 1)
            if random_num == 0:
                num_or_letter = random.choice(string.ascii_uppercase)
                letter_num += 1
            else:
                num_or_letter = random.choice(string.digits)
        else:
            num_or_letter = random.choice(string.digits)
        license_plate_tail += num_or_letter
    area = random.choice(string.ascii_uppercase)
    # 代表行政区域的字母不能是I和O
    while area == 'I' or area == 'O':
        area = random.choice(string.ascii_uppercase)
    return get_license_plate_province() + area + '-' + license_plate_tail


# 随机生成汽车速度30-60km/h
def get_speed():
    return random.uniform(30, 60)


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
    print("mqtt_connect:", ret)
    time.sleep(1)
    while not stop:# and ret == 0:
        info = []
        for i in range(random.randint(100, 200)):
            license_plate = get_license_plate()
            color = get_color()
            car_brand = get_car_brand()
            speed = get_speed()
            car_information = "车牌号:" + license_plate + ";车身颜色:" + color + ";汽车品牌:" + car_brand + ";车速:{:.1f}".format(speed)
            info.append(car_information)
        memory_used = get_memory_used()
        memory_total = get_memory_total()
        network_sent = get_network_sent()
        cpu_usage = get_cpu_usage()
        # base64编码
        info = str(base64.b64encode(str(info).encode('utf-8')), 'utf-8')
        publish_data = {"device_name": device_name, "memory_used": memory_used, "memory_total": memory_total, "cpu_usage": cpu_usage, "network_sent": network_sent, "car_information": "{}".format(info)}
        print(publish_data)
        print("incoming publish:", json.dumps(publish_data))  # dumps()作用是将dict类型的数据转成str
        # 发布到MQTT上
        client.publish(topic=publish_topic, payload=json.dumps(publish_data), qos=0)
        # 每隔1s发布一次信息
        time.sleep(1)
    client.disconnect()
