#!/usr/bin/env python3
#coding:utf-8

#导入需要用到的模块
import time
import json
import psutil
import random
import adafruit_dht
import os
from paho.mqtt import client as mqtt_client
import signal
import sys

device_name = 'dht23'     #自定义，每位学员不能冲突
DHTpin = 17                 #声明使用的dht11的输出引脚BCM编码17
dht_device = adafruit_dht.DHT11(DHTpin)
broker = "edgex_host"       # mqtt代理服务器地址在/etc/hosts内配置
port = 1883				# 端口
keepalive = 60   		# 与代理通信之间允许的最长时间段（以秒为单位）默认60              
topic = "incoming1"  		# 消息主题
client_id = f'mqtt_device_humiture'+device_name  # 客户端id不能重复

#定义个信号量用于强制退出时不影响程序的正常运行
stop = False

def handler(a, b):  # 定义一个signal handling
    global stop
    print("Signal Number:", a, " Frame: ", b)
    stop = True
   
signal.signal(signal.SIGINT, handler)  # 将handle分配给对应信号



#获取dht11的温湿度数据，并将其转换为json格式便于传输
def get_dht():
    try:
       temperature = dht_device.temperature     #获取温度信息
       humidity = dht_device.humidity           #获取湿度信息
       tim = int(time.time())                   #获取当前时间戳
       print("temperature:{} C|humidity:{}".format(temperature,humidity)) #将获取到的温湿度信息打印到屏幕上
       #封装要传输的数据
       info = {'device_name':device_name,'time_stamp':tim,'temperature':temperature,'humidity':humidity}
       #mqtt只能传输字符串数据
       return json.dumps(info)
    except RuntimeError as error:
       print(error)
    except Exception as error:
       dht_device.exit()
       raise error
  


#定义数据库连接函数连接到数据库
def connect_mqtt():
    '''连接mqtt代理服务器'''
    def on_connect(client, userdata, flags, rc):
        '''连接回调函数'''
        # 响应状态码为0表示连接成功
        if rc == 0:
            print("Connected to MQTT OK!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # 连接mqtt代理服务器，并获取连接引用
    client = mqtt_client.Client(client_id)
    client.username_pw_set("admin", "public")		# 连接MQTT的账户和密码
    client.on_connect = on_connect                  #调用on_connect函数返回数据以验证连接成功
    client.connect(broker, port, keepalive)          #调用connect函数输入代理服务器地址、端口号和连接最长时间连接到Mqtt代理服务器   
    return client

#定义pubulish函数用于client发布数据
def publish(client):
    global stop
    '''发布消息'''
    while True:
        '''每隔1秒发布一次服务器信息'''
        msg = get_dht()
        if msg is not  None:
            result = client.publish(topic, msg)
            status = result[0]
            if status == 0:
                print(f"Send `{msg}` to topic `{topic}`")
            else:
                print(f"Failed to send message to topic {topic}")
        time.sleep(2)       #等待2s后再次发送数据
        if stop:            #处理异常退出情况的信号量
            client.disconnect()
            sys.exit()

def run():
    '''运行发布者'''
    client = connect_mqtt()
    # 运行一个线程来自动调用loop()处理网络事件, 非阻塞
    client.loop_start()
    publish(client)

if __name__ == '__main__':
    run()
