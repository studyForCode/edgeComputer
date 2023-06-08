# !/usr/bin/env python3

# coding:utf-8
import signal
import RPi.GPIO as GPIO
import time
import json
# import sys
from paho.mqtt import client as mqtt_client

device_name = '{用户自定义}' # 自定义，每位学员不能冲突，可使用自己的名字作为设备名
colors = [0x00FF, 0xFF00, 0x0FF0, 0xF00F]
LED_RED = 11
LED_GREEN = 12
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_RED, GPIO.OUT)
GPIO.setup(LED_GREEN, GPIO.OUT)
p_R = GPIO.PWM(LED_RED, 2000)
p_G = GPIO.PWM(LED_GREEN, 2000)


broker = "edgex_host"  # mqtt服务器地址在/etc/hosts内修改过
port = 1883  # 端口
keepalive = 60  # 与代理通信之间允许的最长时间段(以秒为单位)，默认60
publish_topic = "incoming"
subscribe_topic = "command" #命令topic
cmd = "ledStatus" #命令名称
# client_id = f"mqtt_device_LED" + device_name
led = 0

# 定义一个信号量用于强制退出时不影响程序的正常运行
stop = False


def handler(a, b):   # 定义一个signal handling
    global stop
    print("Signal Number:", a, "Frame:", b)
    stop = True


signal.signal(signal.SIGINT, handler)   # 将handle分配给对应信号


def on_connect(client, userdata, flags, rc):
    # print("here")
    # 响应状态码为0表示连接成功
    if rc == 0:
        print("Connected to MQTT Broker!\n")
    else:
        print("Failed to connect, return code %d\n", rc)
    # 如果与broker失去连接后重连，仍然会继续订阅ledStatus主题
    client.subscribe(topic=subscribe_topic)


# 初始化占空比为0(熄灭LED灯)
p_R.start(0)
p_G.start(0)


def pwm_map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def set_color(col):
    R_val = col >> 8
    G_val = col & 0x00FF
    # 把0~255同比例缩小到0~100
    R_val = pwm_map(R_val, 0, 255, 0, 100)
    G_val = pwm_map(G_val, 0, 255, 0, 100)
    p_R.ChangeDutyCycle(R_val) # 改变占空比
    p_G.ChangeDutyCycle(G_val)  # 改变占空比


def on_message(client, userdata, msg):
    global led
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
        if rcv_data.get("cmd", None) == cmd:
            ret_data[cmd] = "{}".format(led)
            print("response publish:", json.dumps(ret_data))
    # 处理set请求
    elif rcv_data.get("method", None) == "set":
        led = int(rcv_data.get(cmd, 0))
        print("cmd:", rcv_data.get("cmd", None))
        print("set resource value:", led)
        if led == 1:
            GPIO.output(LED_GREEN, GPIO.HIGH)
            GPIO.output(LED_RED, GPIO.LOW)
            set_color(colors[0])

        # 收到的消息为"2"，打开红灯
        elif led == 2 :
            GPIO.output(LED_GREEN, GPIO.LOW)
            GPIO.output(LED_RED, GPIO.HIGH)
            set_color(colors[1])

        # 收到的消息为"3"，显示混合色
        elif led == 3:
            GPIO.output(LED_GREEN, GPIO.HIGH)
            GPIO.output(LED_RED, GPIO.HIGH)
            set_color(colors[2])

        # 收到的消息为"0"，关闭LED灯
        elif led == 0:
            p_R.start(0)
            p_G.start(0)
    client.publish(topic="response", payload=json.dumps(ret_data), qos=0)


def mqtt_connect(client, username,password,broker_ip,broker_port,keepalive):
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
    client = mqtt_client.Client()
    # 连接mqtt服务器
    ret = mqtt_connect(client, "admin", "public", broker, port, keepalive)
    print("mqtt_connect:", ret)
    time.sleep(1)
    while not stop:# ret==0 and not stop:
        # 构造上报数据
        ret_data = { "name": device_name, "cmd": cmd, "ledStatus": "{}".format(led) }
        print("incoming publish:", json.dumps(ret_data))
        # 发布到MQTT上
        client.publish(topic=publish_topic, payload=json.dumps(ret_data), qos=0)
        time.sleep(3)
    client.disconnect()
