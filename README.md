# edgeComputer
Including ten practical trainings of edge computing projects
1.项目硬件架构及网络拓扑
![image](https://github.com/studyForCode/edgeComputer/assets/135931802/e2f950c4-c62f-45a0-b8c8-eef6fdac87aa)
1)EdgeX Foundry终端节点
嵌入式终端,外接多种传感器,通过WiFi接入
2)路由器、以太网交换机
WiFi路由器负责终端节点的接入,通过以太网交换机将边缘服务器与终端节点相连
3)边缘服务器
位于实训机房,由普通性能的服务器组成,通过以太网交换机与终端节点相连
4)云服务器
位于校内计算中心,由性能较强的服务器组成虚拟机集群,通过校内网与边缘服务器相连
2.项目系统架构
![image](https://github.com/studyForCode/edgeComputer/assets/135931802/72148ffb-2adf-45d2-949e-f4533438c6c8)
1) 终端节点
负责物理数据的采集、监控以及作动等,将采集到的数据通过MQTT服务上报至边端
2) 边缘服务器
通过MQTT服务从终端接收数据,向终端节点下发命令,同以实现对终端节点数据的采集和终端节点的控制,并将必要的数据通过MQTT服务和HTTP接口上报至云服务器
3) 云服务器
负责数据的汇总、分析、聚合统计、管理以及展示
4) PC端
PC端是操作项目的入口,包含了项目浏览、服务器访问以及节点调试等功能
3.终端节点以及传感器
1) 树莓派:
Raspberry Pi（树莓派）是尺寸仅有信用卡大小的一个小型计算机，功能强大，您可以将树莓派连接电视、显示器、键盘等设备使用。树莓派能替代日常桌面计算机的多用途，包括文字处理、电子表格、媒体中心甚至是游戏。因此树莓派有着数量庞大的爱好者进行各种的编程开发，你也可以轻松在网络上找到各种的开发案例。本实验是基于树莓派4B实现。
树莓派构造概览：
![image](https://github.com/studyForCode/edgeComputer/assets/135931802/cfe0038f-fb74-4ed9-ab33-da2cfe7f1817)
树莓派的具体构成如上图所示。树莓派有20个GPIO引脚在树莓派电路板的顶部边缘，是两长排的金属引脚（20Pinx2）。通过它们可以连接诸如发光二极管之类的硬件，并通过树莓派来控制它们开关。下图是关于树莓派GPIO的详细定义。
![image](https://github.com/studyForCode/edgeComputer/assets/135931802/e1b9941e-f75e-4b90-85d0-f229cead4640)
在使用树莓派的GPIO是要注意树莓派官方提供了三种树莓派引脚的编号方式。
（一）使用BOARD编号系统，如上图灰色部分所示。
（二）使用BCM编号系统，如上图橙色部分所示。
（三）使用wiringPi编号系统，如上图青色部分所示。
以上三种方式在实际使用过程中均可以使用，需要注意区分。（注：本实训项目使用BCM编号系统）

项目一  温湿度数据采集上报
==
1.项目背景
   本项目通过终端设备采集温湿度信息,上报至edgex平台,再由edgex平台将温湿度信息上报至云端,并通过云端web服务对采集的数据进行展示。
2.传感器介绍
   1）温湿度传感器(DHT11):
      DHT11温湿度传感器是一款具有已校准数字信号的温湿度复合传感器，其精度湿度为±5%RH，精度温度为±2℃,量程湿度为20~90%RH，量程温度为0~50℃。
      DHT11温湿度传感器使用专门的数字模块采集技术和温湿度传感技术，确保产品具有极高的可靠性和长期的稳定性，具有品质卓越、超快响应、抗干扰能力强、性价比高等优点。
      DHT11规格：
      DHT11有四个引脚，但是其中一个没有被使用到（该引脚默认悬空），所有的模块会简化成3个引脚。如下图所示。
      ![image](https://github.com/studyForCode/edgeComputer/assets/135931802/e8e98aa8-71b5-4d9c-af1e-31ca01a8f3a5)
      ![image](https://github.com/studyForCode/edgeComputer/assets/135931802/04a7eb8c-51d9-4468-b6ee-61eeffa490e5)
3.项目数据流
   1)终端与边端的数据传递
      终端设备将采集到的温湿度信息发送至位于边缘服务器的humiture_incomingtopic中,edgex平台订阅该topic将设备上报的数据交给ekuiper规则引擎处理command_humiture和response两个topic负责edgex命令的下发和设备的响应
   2)边端与云端的数据传递
      规则引擎将处理后的数据发送至位于云端的mqtt broker中的humiture_result topic中,数据采集程序负责将处理后的数据写入数据库供web服务器进行查询和管理。
4.传感器连接
    将温湿度传感器（DHT11）的各引脚与树莓派相连接。
    
注：GPIO17是BCM编号系统的引脚号
连接树莓派与温湿度传感器（DHT11）具体如下图所示：
