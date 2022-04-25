import time
import numpy as np
import pyrealsense2 as rs
import torch
import torch.backends.cudnn as cudnn
import random

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
                d['name'] = row['name']
                d['center_x'], d['center_y'], d['height'] = self.convert_to_realworld(center_x, center_y, center_z)

                ## TEMPORARY ##
                d['height'] = "-63.5"
                ###############
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
        calibration_mat = [[-0.03796503641,  0.9987888303,  -0.03129741865,  0.3244525494],
                    [0.9992437674,  0.03768181288,  -0.009590318112,  -0.1112181919],
                    [-0.008399359137,  -0.0316378473,  -0.9994641051,  0.3920535757],
                    [0,  0,  0,  1]]

        a = np.dot(calibration_mat, coord_mat)
        # convert to mm
        a[2][0] = -0.062
        return str(a[0][0]*1000), str(a[1][0]*1000), str(a[2][0]*1000)
