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
                d['height'] = "-65.3"
                ###############

                ## Calculate 2d orientation ##
                img = color_image[int(row['ymin']-5):int(row['ymax']+5), int(row['xmin']-5):int(row['xmax']+5)]
                angle, _ = estimate_angle(img[:, :, [2, 1, 0]])
                # d['rz'] = str(-estimate_angle(img[:, :, [2, 1, 0]]))
                d['rz'] = str(-angle)
                ##############################
                result_dict.append(d)        
                break

            result = pred.render()[0]
            self.fps = f"{1/(time.time() - start_time):.0f}"
        else:
            result = color_image
            self.fps = "15"

        return result, result_dict

    def convert_to_realworld(self, x, y, z):
        x, y, z = rs.rs2_deproject_pixel_to_point(self.cam_intrinsic, [x, y], z)
        coord_mat = [[x], [y], [z], [1]]
        # calibration matrix
        calibration_mat = [[-0.04690637476,  0.9984116247,  -0.03120928807,  0.2367441775],
            [0.9985854364,  0.04765189589,  0.02358862143,  -0.04215407399],
            [0.0250383356,  -0.03005868383,  -0.9992344856,  0.3805782305],
            [0,  0,  0,  1]]
        s = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0.073], [0, 0, 0, 1]]
        # a = np.dot(calibration_mat, coord_mat)
        a = np.dot(np.dot(calibration_mat, s), coord_mat)
        if a[2][0]*1000 > 0:
            a[2][0] = -0.066
        return str(a[0][0]*1000), str(a[1][0]*1000), str(a[2][0]*1000)
