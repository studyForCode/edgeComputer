**项目二 LED状态监测和控制**

#### 1. 项目背景

​		本项目由终端设备在edgex平台上注册LED监测和控制命令,再通过云端web服务对各个设备的LED状态进行监测和控制。

#### 2.传感器介绍

​      1）双色LED灯源模块

​		将引脚S（绿色）和中间管脚R（红色）连接到树莓派的GPO 接口上，对树莓派进行编程控制，将LED的颜色从红色变为绿色，然后使用PWM混合其他颜色。

​		该模块的原理图如下所示：
![image](https://github.com/studyForCode/edgeComputer/assets/135931802/5a6498af-8361-4cd9-8a89-825778e0cbb4)

![image](https://github.com/studyForCode/edgeComputer/assets/135931802/d9cd2c4b-2e3d-4c7f-a35d-836307512b4a)


#### 3. 项目数据流

##### 1）终端与边端的数据传递

 ![image](https://github.com/studyForCode/edgeComputer/assets/135931802/97c22798-fe40-4ef1-84cc-05dd6d6e4193)


​		终端设备向EdgeX注册LED状态查询和控制命令,该命令通过Command Topic发布,并由终端设备通过Response Topic响应。

##### 2）边端与云端的数据传递

 ![image](https://github.com/studyForCode/edgeComputer/assets/135931802/76d6c89d-00c5-44f0-af24-675fc4925913)


​		用户通过前端页面读取或控制LED灯状态,前端页面接收到用户操作后,将查询/控制请求发送至云端web服务器,web服务器调用EdgeX提供的rest接口对终端进行访问。

#### 4.传感器连接

​		将双色LED模块的各引脚与树莓派相连接。

| 双色LED Pin | Signal   | T形转接板 Pin |
| ----------- | -------- | ------------- |
| S           | Data/Out | 12(GPIO18)    |
| R           | Data/Out | 11(GPIO17)    |
| -           | Ground   | GND           |

注：GPIO17、GPIO18是BCM编号系统的引脚号

连接树莓派与LED灯具体如下图所示：<br>
![image](https://github.com/studyForCode/edgeComputer/assets/135931802/63821dd5-4508-4fb9-a51c-47959a666752)

