import tkinter as tk  
import random
import RPi.GPIO as GPIO
import time
import matplotlib.pyplot as plt
import cv2
from boto3.session import Session
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import argparse
import json
import socket
import datetime
import random
import sys
import os
from PIL import Image,ImageTk

import matplotlib.pyplot as plt

AllowedActions = ['both', 'publish', 'subscribe']
car = False
_pass = False
space = 2
t1=0
ui_factor=-10
position=-10
dist1=-1
tmp_car=0
go_out=0
def showInfo(p1,p2):
    plt.figure("Image",figsize=(20, 16))
    if (p2!=-1):
        plt.imshow(Car[p2])
        plt.axis("off")
        plt.pause(5)
        plt.close("all")
    if(p2==-1):
        plt.axis([0,100,0,100])
        plt.axis("off")
        plt.text(20,50,'You should pay:'+str(p1),fontsize=15)
        plt.pause(5)
        plt.close("all")
        plt.figure(figsize=(20, 16))
        Img=Image.open("pass.png")
        plt.imshow(Img)
        #mng = plt.get_current_fig_manager()
        
        plt.axis("off")
        plt.pause(5)
        plt.close("all")
def customCallback(client, userdata, message):
    global _pass,space,t1,position,ui_factor,dist1,tmp_car,go_out
    print("Received a new message: ")
    print(message.payload)
    str1=str(message.payload, encoding = "utf-8")  
    data=eval(str1)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")
    print("Time for receiving messgae from cloud:{}".format(data["send_time"]-t1))
    if space > 0 or data["status"] == "perminent":
        _pass = True
        print("space:{}".format(space))
    if data["in_and_out"] == "in" and dist1>7.5 and data["status"] == "tmp":
        tmp_car=1
        ui_factor=0
        position=2
    elif data["in_and_out"] == "in" and data["status"] == "tmp":
        tmp_car=1
        ui_factor=0
        position=3
    elif data["in_and_out"] == "out":
        go_out=1
        ui_factor=data["fee"]
        position=-1       
    elif data["status"] == "perminent":
        tmp_car=-1
        ui_factor=0
        position=int(data["car_position"])
    print("in show info the the posiiont and ui_factor should be:",position,ui_factor)
    if _pass == True:
        openGate()
        time.sleep(5)
        closeGate()
        _pass = False
def get_Host_name_IP():
    host_name = socket.gethostname()
    host_ip = socket.gethostbyname(host_name)
    return host_name,host_ip

# Read in command-line parameters

host = "a1pdiz5spt6eed-ats.iot.us-east-1.amazonaws.com"
rootCAPath = "certificate/AmazonRootCA1.pem"
certificatePath = "certificate/f9b033fa3c1bea4b607143e4498204fd1c403d29d789f3ab8756f0c0d343e94e-certificate.pem.crt"
privateKeyPath = "certificate/f9b033fa3c1bea4b607143e4498204fd1c403d29d789f3ab8756f0c0d343e94e-private.pem.key"
port = 8883
clientId = "Rasp"
topic = "$aws/things/car_iot/shadow/name/car_shadow/update"



# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
myAWSIoTMQTTClient.configureEndpoint(host, port)
myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec



myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()

#设置 GPIO 模式为 BCM
GPIO.setmode(GPIO.BCM)
  
#定义 GPIO 引脚
GPIO_TRIGGER = 23
GPIO_ECHO = 24
GPIO_S1_TRIGGER = 5
GPIO_S1_ECHO = 6
GPIO_S2_TRIGGER = 26
GPIO_S2_ECHO = 19
in1 = 16
in2 = 21
ena = 12
  
#设置 GPIO 的工作方式 (IN / OUT)
GPIO.setmode(GPIO.BCM)
GPIO.setup(in1,GPIO.OUT)
GPIO.setup(in2,GPIO.OUT)
GPIO.setup(ena,GPIO.OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)
GPIO.setup(GPIO_S1_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_S1_ECHO, GPIO.IN)
GPIO.setup(GPIO_S2_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_S2_ECHO, GPIO.IN)
GPIO.output(in1,GPIO.LOW)
GPIO.output(in2,GPIO.LOW)
p=GPIO.PWM(ena,1000)
p.start(25)

aws_key = "AKIA3CPRYB4EAIHAFDUT"# 【你的 aws_access_key】 
aws_secret = "+7hoL+U1MemwXHamrzNm5c99zvONFyQ5uwZuRDEu" # 【你的 aws_secret_key】 
session = Session(aws_access_key_id=aws_key, 
aws_secret_access_key=aws_secret, 
region_name="us-east-1") # 此处根据自己的 s3 地区位置改变 
s3 = session.resource("s3") 
client = session.client("s3") 
bucket = "smartpark" # 【你 bucket 的名字】 # 首先需要保证 s3 上已经存在该存储桶，否则报错 


def distance(tri,echo):
    # 发送高电平信号到 Trig 引脚
    GPIO.output(tri, True)
  
    # 持续 10 us 
    time.sleep(0.00001)
    GPIO.output(tri, False)
  
    start_time = time.time()
    stop_time = time.time()
  
    # 记录发送超声波的时刻1
    while GPIO.input(echo) == 0:
        start_time = time.time()
  
    # 记录接收到返回超声波的时刻2
    while GPIO.input(echo) == 1:
        stop_time = time.time()
  
    # 计算超声波的往返时间 = 时刻2 - 时刻1
    time_elapsed = stop_time - start_time
    # 声波的速度为 343m/s， 转化为 34300cm/s。
    distance = (time_elapsed * 34300) / 2
  
    return distance
def uploadimage():
    upload_data = open("test.jpg", "rb") 
    upload_key = "images/test.jpg" 
    file_obj = s3.Bucket(bucket).put_object(Key=upload_key, Body=upload_data) 
    print(file_obj)

def openGate():
    GPIO.output(in1,GPIO.HIGH)
    time.sleep(0.2)
    GPIO.output(in1,GPIO.LOW)
    t2 = time.time() - t1
    print("{:.6f}".format(t2))
def closeGate():
    GPIO.output(in2,GPIO.HIGH)
    time.sleep(0.2)
    GPIO.output(in2,GPIO.LOW)

    
class UpdateLabel():
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("Show Image")
        self.win.minsize(1000, 1000)
        self.Canvas=tk.Canvas(self.win,height=2000,width=2000,bg="white")
        self.tk_var = tk.StringVar()
        self.tk_var.set("0")
        imgpass= (Image.open("pass.png"))
        resized_pass= imgpass.resize((800,500), Image.ANTIALIAS)
        img1= (Image.open("car_park1.png"))
        resized1= img1.resize((800,500), Image.ANTIALIAS)
        img2= (Image.open("car_park2.png"))
        resized2= img2.resize((800,500), Image.ANTIALIAS)
        img3= (Image.open("car_park3.png"))
        resized3= img3.resize((800,500), Image.ANTIALIAS)
        img4= (Image.open("car_park4.png"))
        resized4= img4.resize((800,500), Image.ANTIALIAS)
        imgfull= (Image.open("full.png"))
        resizedfull= imgfull.resize((800,500), Image.ANTIALIAS)
        imgava= (Image.open("ava.jpg"))
        resizedava= imgava.resize((800,500), Image.ANTIALIAS)
        self.ph_pass=ImageTk.PhotoImage(resized_pass)
        self.ph_full=ImageTk.PhotoImage(resizedfull)
        self.ph_ava=ImageTk.PhotoImage(resizedava)
        self.ph_1=ImageTk.PhotoImage(resized1)
        self.ph_2=ImageTk.PhotoImage(resized2)
        self.ph_3=ImageTk.PhotoImage(resized3)
        self.ph_4=ImageTk.PhotoImage(resized4)
        self.showText=0
        self.showImage=0
        self.flag=0
        self.showAva=0
        self.showfull=0
        self.pay=2
        self.sleep=0
        self.start_tk=-1
        self.updater()
        self.win.mainloop()
        
    def updater(self):
        global _pass,car,position,ui_factor,dist1,space,tmp_car,go_out
        dist1 = distance(GPIO_S1_TRIGGER,GPIO_S1_ECHO)
        dist2 = distance(GPIO_S2_TRIGGER,GPIO_S2_ECHO)
        
        dist = distance(GPIO_TRIGGER,GPIO_ECHO)

        if dist < 15 and car == False:
            t1 = time.time()
            capture = cv2.VideoCapture(0)
            ret, frame = capture.read()
            cv2.imwrite('test.jpg',frame)
            print("capture")
            capture.release()
            uploadimage()
            car = True;
        elif dist > 15:
            car = False
        time.sleep(1)
        
        if dist1<5 and dist2<5:
            space=0

        elif dist1>5 and dist2>5:
            space=2
        else:
            space=1
        print("in updater the the posiiont and ui_factor should be:",position,ui_factor)
        if (self.start_tk>-1):
            self.start_tk=self.start_tk+1
        if (go_out!=1 and tmp_car==1 and space==0):
                self.showFull()
                self.win.after(100,self.updater)
                return;
        if (self.start_tk==2):
            if (space==0):
                self.showFull()
            else:
                self.showA()
            position=-10
            ui_factor=-10
            self.start_tk=-10
        if (position==-10 and ui_factor==-10 and space==0):
            self.showFull()
            
            self.win.after(100,self.updater)
            return
        if (position==-10 and ui_factor==-10 and space!=0):
            self.showA()
            
            self.win.after(100,self.updater)
            return 
        if (position!=-1):
           self.Image(position)
        if(position==-1):
            self.Word(ui_factor)
        print(self.start_tk)
        self.win.after(100,self.updater)
        
    def Image(self,p2):
        self.Canvas.delete(tk.ALL)
        if (p2>=0):
            self.showImage=self.Canvas.create_image((1000, 500),image=eval("self.ph_"+str(p2+1)))
            self.Canvas.pack()
        if (self.start_tk<0):
            self.start_tk=0
        self.flag=1
        self.showAva=1
    def Word(self,pay): 
        self.Canvas.delete(tk.ALL)
        print("In Word the position result should be:",pay)
        self.showText=self.Canvas.create_text((1000,500),text="You should pay:"+str(pay),font=("Purisa",30))
        if (self.start_tk<0):
            self.start_tk=0
        self.showAva=1
        self.Canvas.pack()

    def showA(self):
        self.Canvas.delete(tk.ALL)
        self.start_tk=-100
        self.showImage=self.Canvas.create_image((1000, 500),image=self.ph_ava)
        self.Canvas.pack()
    def showFull(self):
        self.Canvas.delete(tk.ALL)
        self.start_tk=-100
        self.showImage=self.Canvas.create_image((1000, 500),image=self.ph_full)
        self.Canvas.pack()
    def showPass(self):
        self.Canvas.delete(tk.ALL)
        if (self.start_tk<0):
            self.start_tk=0
        self.showImage=self.Canvas.create_image((1000, 500),image=self.ph_pass)
        self.Canvas.pack()
UL=UpdateLabel()
