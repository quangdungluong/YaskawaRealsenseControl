import time
import numpy as np
import pyrealsense2 as rs
import torch
import torch.backends.cudnn as cudnn
import random
from estimate2d import estimate_angle

class CameraControl:
    def __init__(self):
        self.detect_flag = True
        self.weights = './model/best_n.pt'
        self.cur_weights = './model/best_n.pt'
        self.model = torch.hub.load('E:/yolov5', 'custom', path=self.cur_weights, source='local')
        self.model.conf = 0.7
        cudnn.benchmark = True
        self.result = None
        self.result_dict = dict()
        self.fps = None

        ############### Realsense ###############
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.rgb8, 30)                                                         
        align_to = rs.stream.color
        self.align = rs.align(align_to)
        self.cam_intrinsic = None       
    
    def process(self, color_image, depth_frame):
        """
        Process image and extract real world coordinate of objects
        """
        result_dict = []
        start_time = time.time()
        if (self.detect_flag):
            pred = self.model(color_image)
            json = pred.pandas().xyxy[0].sort_values('xmax', ascending=False).to_dict(orient="records") # sort right -> left
            for row in json:
                d = dict()
                center_x = (row['xmin'] + row['xmax'])/2
                center_y = (row['ymin'] + row['ymax'])/2
                center_z = depth_frame.get_distance(int(center_x), int(center_y))
                d['class'] = row['class']
                d['center_x'], d['center_y'], d['height'] = self.convert_to_realworld(center_x, center_y, center_z)

                ## TEMPORARY ##
                d['height'] = "-65.5"
                ###############

                ## Calculate 2d orientation ##
                img = color_image[int(row['ymin']-10):int(row['ymax']+10), int(row['xmin']-10):int(row['xmax']+10)]
                d['rz'] = str(-estimate_angle(img[:, :, [2, 1, 0]]))
                ##############################
                result_dict.append(d)        

            result = pred.render()[0]
            self.fps = f"{1/(time.time() - start_time):.0f}"
        else:
            result = color_image
            self.fps = "15"

        return result, result_dict

    def convert_to_realworld(self, x, y, z):
        x, y, z = rs.rs2_deproject_pixel_to_point(self.cam_intrinsic, [x, y], z)
        coord_mat = [[x], [y], [z], [1]]
        calibration_mat = [[-0.06414223941,  0.9979230425,  -0.005947640776,  0.3180929458],
                    [0.9979403731,  0.06413578406,  -0.001270011597,  -0.03084779342],
                    [-0.0008859172322,  -0.006016852243,  -0.9999815061,  0.3921178095],
                    [0,  0,  0,  1]]

        a = np.dot(calibration_mat, coord_mat)
        # convert to mm
        a[2][0] = -0.062
        return str(a[0][0]*1000), str(a[1][0]*1000), str(a[2][0]*1000)
