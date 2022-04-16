import numpy as np
import pyrealsense2 as rs
import torch
import torch.backends.cudnn as cudnn

model = torch.hub.load('E:/yolov5', 'custom', path='./model/best_n.pt', source='local')
model.conf = 0.7

def convert_to_realworld(intrs, x, y, z):
    x, y, z = rs.rs2_deproject_pixel_to_point(intrs, [x, y], z)
    cam_mat = [[x], [y], [z], [1]]
    calib = [[-0.03796503641,  0.9987888303,  -0.03129741865,  0.3244525494],
                    [0.9992437674,  0.03768181288,  -0.009590318112,  -0.1112181919],
                    [-0.008399359137,  -0.0316378473,  -0.9994641051,  0.3920535757],
                    [0,  0,  0,  1]]
    a = np.dot(calib, cam_mat)
    return a[0][0], a[1][0], a[2][0]

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

frames = pipeline.wait_for_frames()
frames = align.process(frames)
color_frame = frames.get_color_frame()
depth_frame = frames.get_depth_frame()
color_image = np.asanyarray(color_frame.get_data())
print("Color")
result, result_dict = process(color_intrs, color_image, depth_frame)
print(result_dict)

print("Depth")

result, result_dict = process(depth_intrs, color_image, depth_frame)
print(result_dict)