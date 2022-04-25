from calendar import c
from traceback import print_tb
from CameraControl import *
from RobotControl import *
import cv2
import time
import glob
import csv
import numpy as np
from PyQt5.QtCore import pyqtSignal, QThread, QTimer
import math
from UART import *

class Main_loop(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    send_fps = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.r = RobotControl()
        self.camera = CameraControl() 
        self.picking = False
        self.destXYZ_obj = [["-11.53", "-258.413", "-34.826"], ["-11.53", "-258.413", "-34.826"], ["-11.53", "-258.413", "-34.826"], ["-11.53", "-258.413", "-34.826"], ["-11.53", "-258.413", "-34.826"], ["-11.53", "-258.413", "-34.826"]]
        self.cam_flag = False
        self.auto_run = False
        self.XYZ_obj = []
        self.v_robot = 200
        ## Reset conveyor
        self.r.writeByte(2, 1)
        self.v = 0
        self.c = 0
        self.serial = serial.Serial('COM4', 9600, timeout=0.001)
        self.uart = ReadFromSerial(self.serial)
        self.count = True

    def run(self):
        self.r.writeByte(1, 0)
        self.r.writeByte(5, 0)
        self.auto_run = True
        self.r.servoON()
        self.r.Write_Robot_XYZ(xc, yc, zc)
        self.r.mainJobStart()

        while True:
            if self.auto_run and self.cam_flag and self.picking and len(self.XYZ_obj) > 0:
                x, y, z, id = self.XYZ_obj[0]['center_x'], self.XYZ_obj[0]['center_y'], self.XYZ_obj[0]['height'], self.XYZ_obj[0]['name']
                self.XYZ_obj = []
                # velocity = 30
                # t1 = 1.31 # 3.11 work fine
                # y = str(float(y) + velocity * t1)
                x, y, z = self.estimatePos(xc, yc, zc, x, y, z)
                if (float(y) > -190 and float(y) < 110):
                    dest_x, dest_y, dest_z = self.destXYZ_obj[0]
                    print(x, y, z)
        
                    self.r.writePos(30, x, y, z)
                    self.r.writePos(33, x, y, "10")
                    self.r.writePos(31, xc, yc, "20")
                    self.r.writePos(36, dest_x, dest_y, dest_z)
                    self.r.writeByte(5, 1)
                    time.sleep(5)
                    self.picking = False
                else:
                    self.picking = False
                
            elif not self.auto_run:
                break

            else:
                time.sleep(0.000001)

    def camera_run(self):
        self.cam_flag = True
        profile = self.camera.pipeline.start(self.camera.config)
        stream_profile_depth = profile.get_stream(rs.stream.depth)
        stream_profile_color = profile.get_stream(rs.stream.color)
        self.camera.cam_intrinsic = stream_profile_color.as_video_stream_profile().get_intrinsics()

        if (self.camera.cur_weights != self.camera.weights):
            self.camera.cur_weights = self.camera.weights
            self.camera.model = torch.hub.load('E:/yolov5', 'custom', path=self.camera.cur_weights, source='local')

        while True:
            try:
                self.c = float(self.uart.read_one_struct())*10
            except:
                self.c = -1
            frames = self.camera.pipeline.wait_for_frames()
            frames = self.camera.align.process(frames)
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            if not depth_frame or not color_frame:
                continue

            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            result, XYZ_obj = self.camera.process(color_image, depth_frame)
            if self.picking == False and len(XYZ_obj)!=0:
                self.picking = True
                self.XYZ_obj = XYZ_obj

            self.change_pixmap_signal.emit(result)
            self.send_fps.emit(self.camera.fps)

            if not self.cam_flag:
                break

    def read_conveyor(self):
        self.serial.write(b'1')
        v = float(self.uart.read_one_struct())*10
        return v

    def estimatePos(self, xc, yc, zc, x0, y0, z0):
        """
        xc, yc, zc: robot home pos
        x0, y0, z0: obj home pos
        x, y, z: finding point, x=x0, z=z0
        """
        xc, yc, zc, x0, y0, z0 = float(xc), float(yc), float(zc), float(x0), float(y0), float(z0)
        v_conveyor = self.c
        print(v_conveyor)
        v_robot = self.v
        delta_y = abs(yc-y0)
        a = v_robot**2 - v_conveyor**2
        b = 2*delta_y*v_conveyor
        c = -(zc-z0)**2 - delta_y**2

        delta = b**2 - 4*a*c
        t = (-b + math.sqrt(delta))/(2*a)
        y = y0 + v_conveyor*t
        return x0, y, z0

    # def checkDone(self):
    #     data = self.r.ReadByte(2)
    #     if (len(data)==33): print(data[32])
    #     if (len(data)==33 and data[32]==0):
    #         return
    #     else:
    #         self.checkDone()

    def checkDone(self):
        data = self.r.ReadByte(2)
        
        if (len(data)==33 and data[32]==1):
            return True
        elif (len(data)==33 and data[32]==0):
            return False