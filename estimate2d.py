import cv2
from math import atan2, cos, sin, sqrt, pi
import numpy as np
 
def estimate_angle(img):
    try:
        img = cv2.resize(img, (224, 224))
        # cv2.imshow("orig", img)
        # cv2.imwrite('./2d/orig.png', img)
        # Convert image to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # cv2.imshow("gray", gray)
        # cv2.imwrite('./2d/gray.png', gray)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        # cv2.imshow('blur', blurred)
        # cv2.imwrite('./2d/blur.png', blurred)
        # Convert image to binary
        _, bw = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        # bw = cv2.adaptiveThreshold(blurred, 255,
	        # cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 5)
        # cv2.imshow("bw", bw)
        # cv2.imwrite('./2d/bin.png', bw)
        # cv2.waitKey(0)
        # Find all the contours in the thresholded image
        contours, _ = cv2.findContours(bw, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

        for i, c in enumerate(contours):
            # Calculate the area of each contour
            area = cv2.contourArea(c)

            # Ignore contours that are too small or too large
            if area < 10000 or 100000 < area:
                continue

            # cv2.minAreaRect returns:
            # (center(x, y), (width, height), angle of rotation) = cv2.minAreaRect(c)
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

            cv2.drawContours(img, [box], 0, (0,0,255), 2)
            # cv2.imshow('Output Image', img)
            # cv2.imwrite('./2d/out.png', img)
            # cv2.waitKey(0)

            if angle == None:
                continue
            else:
                return angle, center
        return 0, (0, 0)
    except:
        return 0, (0, 0)

if __name__ == "__main__":
    img = cv2.imread('./image/test.PNG')
    angle, center = estimate_angle(img)
    print(angle)
    print(center)