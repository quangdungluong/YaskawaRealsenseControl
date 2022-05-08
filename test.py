import torch
import pyrealsense2 as rs
import numpy as np
import cv2
import time
import math
from estimate2d import estimate_angle


def find_plane(points):
    c = np.mean(points, axis=0)
    r0 = points - c
    u, s, v = np.linalg.svd(r0)
    nv = v[-1, :]
    ds = np.dot(points, nv)
    param = np.r_[nv, -np.mean(ds)]
    return param

def process(depth_frame, xmin, xmax, ymin, ymax):
    center_x = (xmin+xmax)/2
    center_y = (ymin+ymax)/2
    offset_x = (xmax-xmin)/15
    offset_y = (ymax-ymin)/15

    points = []
    for i in range(-1, 2):
        for j in range(-1, 2):
            x = center_x + i * offset_x
            y = center_y + j * offset_y
            z = depth_frame.get_distance(int(x), int(y))*1000
            points.append([x,y,z])

    param = find_plane(points)
    alpha = math.atan(param[2]/param[0])*180/math.pi
    if(alpha < 0):
        alpha = alpha + 90
    else:
        alpha = alpha - 90

    gamma = math.atan(param[2]/param[1])*180/math.pi
    if(gamma < 0):
        gamma = gamma + 90
    else:
        gamma = gamma - 90
    return alpha, gamma

if __name__=="__main__":
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.rgb8, 30)                                                         
    align_to = rs.stream.color
    align = rs.align(align_to)

    profile = pipeline.start(config)
    stream_profile_depth = profile.get_stream(rs.stream.depth)
    stream_profile_color = profile.get_stream(rs.stream.color)
    cam_intrinsic = stream_profile_color.as_video_stream_profile().get_intrinsics()
    while True:
        frames = pipeline.wait_for_frames()
        frames = align.process(frames)
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            continue

        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        x1 = 208
        x2 = 231
        y = 156

        alpha, gamma = process(depth_frame, 250, 300, 135, 170)
        print(alpha, gamma)

        cv2.imshow("IMG", color_image[:, :, [2, 1, 0]])
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break