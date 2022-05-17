import numpy as np
import pyrealsense2 as rs
import torch
import torch.backends.cudnn as cudnn
from estimate2d import *

model = torch.hub.load('E:/yolov5', 'custom', path='./model/best_n.pt', source='local')
model.conf = 0.7
model.iou = 0.45


def convert_to_realworld(intrs, x, y, z):
    x, y, z = rs.rs2_deproject_pixel_to_point(intrs, [x, y], z)
    cam_mat = [[x], [y], [z], [1]]
    calib = [[-0.04690637476,  0.9984116247,  -0.03120928807,  0.2367441775],
            [0.9985854364,  0.04765189589,  0.02358862143,  -0.04215407399],
            [0.0250383356,  -0.03005868383,  -0.9992344856,  0.3805782305],
            [0,  0,  0,  1]]
    # calib = [[-0.04613245159,  0.9984472211,  -0.03122408622,  0.2369195788],
    #         [0.9986193135,  0.04688149984,  0.02369792658,  -0.04182643278],
    #         [0.02512496094,  -0.03008773209,  -0.999231437,  0.3801365053],
    #         [0,  0,  0,  1]]
    s = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0.072], [0, 0, 0, 1]]
    # a = np.dot(calib, cam_mat)
    a = np.dot(np.dot(calib, s), cam_mat)
    return a[0][0]*1000, a[1][0]*1000, a[2][0]*1000

def process(intrs, color_image, depth_frame):
        result_dict = []
        if (1):
            image = color_image
            pred = model(image)
            json = pred.pandas().xyxy[0].sort_values('xmax', ascending=False).to_dict(orient="records") # sort right - to
            for row in json:
                d = dict()
                center_x = (row['xmin'] + row['xmax'])/2
                center_y = (row['ymin'] + row['ymax'])/2
                center_z = depth_frame.get_distance(int(center_x), int(center_y))
                d['name'] = row['name']
                d['center_x'], d['center_y'], d['height'] = convert_to_realworld(intrs, center_x, center_y, center_z)
                d['center_z'] = center_z
                img = color_image[int(row['ymin']-5):int(row['ymax']+5), int(row['xmin']-5):int(row['xmax']+5)]
                angle, _ = estimate_angle(img[:, :, [2, 1, 0]])
                d['rz'] = str(-angle)
                result_dict.append(d)                

            result = pred.render()[0]

        return result, result_dict

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.rgb8, 30)

profile = pipeline.start(config)
stream_profile_depth = profile.get_stream(rs.stream.depth)
stream_profile_color = profile.get_stream(rs.stream.color)
depth_intrs = stream_profile_depth.as_video_stream_profile().get_intrinsics()
color_intrs = stream_profile_color.as_video_stream_profile().get_intrinsics()
align_to = rs.stream.color
align = rs.align(align_to)

for i in range(300):
    frames = pipeline.wait_for_frames()
    frames = align.process(frames)
    color_frame = frames.get_color_frame()
    depth_frame = frames.get_depth_frame()
    color_image = np.asanyarray(color_frame.get_data())

print("Color")
result, result_dict = process(color_intrs, color_image, depth_frame)
print(result_dict)