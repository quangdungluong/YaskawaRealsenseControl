import cv2
from math import atan2, cos, sin, sqrt, pi
import numpy as np
 
def estimate_angle(img):
    img = cv2.resize(img, (448, 448))
    # cv2.imshow("orig", img)
    # Convert image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # cv2.imshow("gray", gray)
    # Convert image to binary
    _, bw = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # cv2.imshow("bw", bw)
    # Find all the contours in the thresholded image
    contours, _ = cv2.findContours(bw, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    # cv2.waitKey(0)
    for i, c in enumerate(contours):
        # Calculate the area of each contour
        area = cv2.contourArea(c)
        # Ignore contours that are too small or too large
        if area < 10000 or 100000 < area:
            continue
        # cv2.minAreaRect returns:
        # (center(x, y), (width, height), angle of rotation) = cv22.minAreaRect(c)
        rect = cv2.minAreaRect(c)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        # Retrieve the key parameters of the rotated bounding box
        center = (int(rect[0][0]),int(rect[0][1])) 
        width = int(rect[1][0])
        height = int(rect[1][1])
        angle = rect[2]
        if width < height:
            angle = 90 - angle
        else:
            angle = -angle
        if angle == None:
            continue
        else:
            return angle
    return 0

# if __name__ == "__main__":
#     img = cv2.imread('./image/test.PNG')
#     estimate_angle(img)