from CameraControl import *
from RobotControl import *
import cv2
import time
import numpy as np
from PyQt5.QtCore import pyqtSignal, QThread
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
        self.destXYZ_obj = [["-33.009", "-256.58", "-55.6"], ["44.593", "-256.58", "-55.6"], ["113.211", "-256.58", "-55.6"], 
        ["-33.009", "-205.783", "-55.6"], ["44.577", "-205.783", "-55.6"], ["113.211", "-205.783", "-55.6"]]
        self.offset = [0, 0, 0, 0, 0, 0]
        self.cam_flag = False
        self.auto_run = False
        self.XYZ_obj = []
        self.v = 2000
        self.c = 0
        self.serial = serial.Serial('COM4', 9600, timeout=0.0001)
        self.uart = ReadFromSerial(self.serial)
        self.firstPick = True # fix lagging when first pick
        self.r_x = xc
        self.r_y = yc
        self.r_z = zc
        self.pause = False
        self.delay_t = 4.32

    def run(self):
        self.r.writeDouble(1, self.v)
        self.r.writeByte(5, 0)
        self.auto_run = True
        self.r.servoON()
        # self.r.Write_Robot_XYZ(xc, yc, zc)
        self.r.Write_Robot_XYZ(x_idle, y_idle, "20")
        self.r.mainJobStart()

        while True:
            if self.auto_run and self.cam_flag and self.picking and len(self.XYZ_obj) > 0 and not self.pause:
                x, y, z, rz, id = self.XYZ_obj[0]['center_x'], self.XYZ_obj[0]['center_y'], self.XYZ_obj[0]['height'], self.XYZ_obj[0]['rz'], self.XYZ_obj[0]['class']
                self.XYZ_obj = []
                # x, y, z = self.estimatePos(self.r_x, self.r_y, self.r_z, x, y, z)
                # x, y, z = self.estimatePos(xc, yc, zc, x, y, z)
                x, y, z = self.estimatePos(x_idle, y_idle, zc, x, y, z)
                # if (float(y) > -190 and float(y) < 110):
                if (float(y) > -140 and float(y) < 120 and float(x) > 200 and float(x) < 290):
                    dest_x, dest_y, dest_z = self.destXYZ_obj[id]
                    dest_z = "-20"
                    offset = self.offset[id]
                    dest_x = str(float(dest_x) - 30*(offset%3))
                    dest_y = str(float(dest_y) + 30*(offset//3))
                    dest_z = str(float(dest_z) + 25*(offset//6))
                    # self.offset[id] += 1
                    print(x, y, z)

                    self.r.writePosition(30, x, y, z)
                    self.r.writePosition(31, x, y, "5")
                    self.r.writePosition(32, dest_x, dest_y, "10", rz=rz)
                    self.r.writePosition(33, dest_x, dest_y, dest_z, rz=rz)
                    # self.r.writePosition(34, xc, yc, "20")
                    self.r.writePosition(34, x_idle, y_idle, "20")
                    self.r.writePosition(35, "156", "-90", "20")
                    self.r.writeByte(5, 1)
                    self.r_z = "20"
                    # time.sleep(4.8)
                    time.sleep(self.delay_t)
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
        # self.camera.cam_intrinsic = stream_profile_depth.as_video_stream_profile().get_intrinsics()

        if (self.camera.cur_weights != self.camera.weights):
            self.camera.cur_weights = self.camera.weights
            self.camera.model = torch.hub.load('E:/yolov5', 'custom', path=self.camera.cur_weights, source='local')
            self.camera.model.conf = 0.7

        while True:
            frames = self.camera.pipeline.wait_for_frames()
            frames = self.camera.align.process(frames)
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            if not depth_frame or not color_frame:
                continue

            # depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            result, XYZ_obj = self.camera.process(color_image, depth_frame)
            if self.picking == False and len(XYZ_obj)!=0:
                if self.firstPick:
                    self.firstPick = False
                    continue
                else:
                    self.picking = True
                    self.XYZ_obj = XYZ_obj

            self.change_pixmap_signal.emit(result)
            self.send_fps.emit(self.camera.fps)

            if not self.cam_flag:
                break

    def read_conveyor(self):
        self.serial.write(b'1')
        try:
            v = float(self.uart.read_one_struct())*10
        except:
            v = 100
        while(v > 50):
            self.serial.write(b'1')
            try:
                v = float(self.uart.read_one_struct())*10
            except:
                v = 100
        return v
        # return 0

    def estimatePos(self, xc, yc, zc, x0, y0, z0):
        """
        xc, yc, zc: robot home pos
        x0, y0, z0: obj home pos
        x, y, z: finding point, x=x0, z=z0
        """
        xc, yc, zc, x0, y0, z0 = float(xc), float(yc), float(zc), float(x0), float(y0), float(z0)
        v_conveyor = self.read_conveyor()
        v_robot = self.v/10
        print(v_conveyor)
        delta_y = abs(yc-y0)
        a = v_robot**2 - v_conveyor**2
        b = 2*delta_y*v_conveyor
        c = -(zc-z0)**2 - delta_y**2

        delta = b**2 - 4*a*c
        t = (-b + math.sqrt(delta))/(2*a)
        y = y0 + v_conveyor*t
        return x0, y, z0