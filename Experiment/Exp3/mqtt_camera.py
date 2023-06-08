# !/usr/bin/env python3
# coding:utf-8

# 导入需要用到的模块
import json
import RPi.GPIO as GPIO
import signal
import paho.mqtt.client as mqtt
import time
import base64
from picamera import PiCamera

device_name = '{用户自定义}'   # 自定义，每位学员不能冲突
color = 0x00FF
LED_RED = 11
LED_GREEN = 12
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
# 设置引脚为输出模式
GPIO.setup(LED_RED, GPIO.OUT)
GPIO.setup(LED_GREEN, GPIO.OUT)
# 设置频率为2kHz
p_R = GPIO.PWM(LED_RED, 2000)
p_G = GPIO.PWM(LED_GREEN, 2000)

broker = "edgex_host"  # mqtt代理服务器地址在/etc/hosts内修改过
port = 1883  # 端口
keepalive = 60  # 与代理通信之间允许的最长时间段(以秒为单位)，默认60
publish_topic = "incoming3"
subscribe_topic = "command3"
led = 0  # 指示LED灯的状态，0表示灯灭，1表示灯亮

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


def on_connect(client, userdata, flags, rc):
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
    p_R.ChangeDutyCycle(R_val)  # 改变占空比
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
        if rcv_data.get("cmd", None) == "ledStatus":
            ret_data["ledStatus"] = "{}".format(led)
            print("response publish:", json.dumps(ret_data))
    # 处理set请求
    elif rcv_data.get("method", None) == "set":
        led = int(rcv_data.get("ledStatus", 0))
        print("cmd:", rcv_data.get("cmd", None))
        print("set resource value:", led)
        # 收到的消息为"1"，打开绿灯
        if led == 1:
            GPIO.output(LED_GREEN, GPIO.HIGH)
            GPIO.output(LED_RED, GPIO.LOW)
            set_color(color)

            time.sleep(1)  # 使灯亮1秒之后关闭
            # 将占空比设置为0(熄灭LED灯)
            p_R.start(0)
            p_G.start(0)
            led = 0

    client.publish(topic="response", payload=json.dumps(ret_data), qos=0)


# 照相函数
def get_image():
    camera.resolution = (1024, 768)  # 摄像界面为1024*768
    camera.start_preview()  # 开始摄像
    camera.capture('faceimage.jpg')  # 拍照并保存
    camera.stop_preview()


# 对图片的格式进行转换
def trans_image():
    f = open('faceimage.jpg', 'rb')
    img = base64.b64encode(f.read())
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
    while not stop and ret == 0:
        if input("请按下回车键拍照") == '':
            # 拍摄照片
            img = get_image()
            # 将照片格式转换为base64编码
            img = trans_image()
            # 上报照片到mqtt
            publish_data = {"device_name": device_name, "ledStatus": led, "image": "{}".format(img)}
            # print("incoming publish:", json.dumps(publish_data))  # dumps()作用是将dict类型的数据转成str
            # 发布到MQTT上
            client.publish(topic=publish_topic, payload=json.dumps(publish_data), qos=0)
            time.sleep(1)
    client.disconnect()
