from CameraControl import *
from RobotControl import *
import cv2
import time
import glob
import csv
import numpy as np
from PyQt5.QtCore import pyqtSignal, QThread

class Main_loop(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    send_fps = pyqtSignal(str)
    send_pos = pyqtSignal(np.ndarray)
    send_msg = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.r = RobotControl()         # Initialize the picking connection
        self.camera = CameraControl()   # Initialize the Image Processing 
        self.picking = False              # Robot picking enable
        self.destXYZ_obj = [[100, 100, -50], [200, 200, -50], [200, 100, -60]]
        self.dx = []                    # object moves in 1 frame (pixel)
        self.dt = []                    # time between object-found frames
        self.v = 0.0000                 # object velocity - dynamic
        self.t_gap = 4.0000             # robot_run_ picking time
        self.cam_flag = False           # Need for webcam thread
        self.go_home = False            # flag for go home action
        self.XYZ_obj = []               # Postion of picking object
        self.X = ["200", "220", "250"]
        self.Y = ["100", "70", "-100", "-70", "0"]
        self.Z = ["-50", "-60", "50", "100"]

        ## Reset conveyor
        self.r.writeByte(2, 0)

    def robot_home(self):
        while(self.cam_flag):
            if (self.go_home):
                self.r.CheckToolOff()
                self.r.Write_Robot_XYZ(xc, yc, zc, "180.0000")
                time.sleep(0.2)
                self.go_home = False

    def run(self):
        self.r.writeByte(1, 0)
        self.r.writeByte(5, 0)
        # self.r.writeByte(2, 0)
        self.r.mainJob()
        self.auto_run = True
        self.r.servoON()
        while(self.cam_flag and self.auto_run):
            if (self.picking and len(self.XYZ_obj) > 0):
                try:
                    # Get object position and destination position
                    x, y, z = self.XYZ_obj[0]['center_x'], self.XYZ_obj[0]['center_y'], self.XYZ_obj[0]['height']
                    dest_x, dest_y, dest_z = "-11.53", "-258.413", "-34.826"
                    self.XYZ_obj.pop(0)
                    print(x, y, z)
                    
                    self.r.writePos(30, x, y, z)
                    self.r.writePos(36, dest_x, dest_y, dest_z)
                    self.r.writeByte(5, 1)
                    self.r.writeByte(5, 0)

                    self.picking = False
                    self.send_msg.emit("Done...")

                except:
                    pass
            else:
                time.sleep(0.0001)

    def camera_run(self):
        self.cam_flag = True

        profile = self.camera.pipeline.start(self.camera.config)
        stream_profile_depth = profile.get_stream(rs.stream.depth)
        stream_profile_color = profile.get_stream(rs.stream.color)
        self.camera.intrs = stream_profile_color.as_video_stream_profile().get_intrinsics()
        
        while self.cam_flag:
            # Changed model
            if (self.camera.cur_weights != self.camera.weights):
                self.camera.cur_weights = self.camera.weights
                self.camera.model = torch.hub.load('E:/yolov5', 'custom', path=self.camera.cur_weights, source='local')

            frames = self.camera.pipeline.wait_for_frames()
            frames = self.camera.align.process(frames)
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            if not depth_frame or not color_frame:
                continue

            # Convert images to numpy arrays
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            self.camera.result, self.XYZ_obj = self.camera.process(color_image, depth_frame)
            
            if (not self.picking) and (self.XYZ_obj):
                self.picking = True

            self.change_pixmap_signal.emit(self.camera.result)
            self.send_fps.emit(self.camera.fps)      