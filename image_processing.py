from json.tool import main
from tkinter.messagebox import NO
from typing import final
import numpy as np
import cv2
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib import colors




def detect_table_Color(img):

    height,width = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
   
    #table segmentation
    light_blue = (105, 70, 70)
    dark_blue = (128, 255, 255)
    
    mask_blue = cv2.inRange(hsv, light_blue, dark_blue)
  
    # final_mask = mask_orange + mask_blue #segment table and ball
    final_mask = mask_blue # segment only table
  
   
    final_mask = cv2.medianBlur(final_mask, ksize = 7)
    pesudo_mask = np.zeros((height,width), np.uint8)

    #draw contours        
    contours, hierarchy = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    if len(contours) != 0:
        c = max(contours, key = cv2.contourArea)
        hull = cv2.convexHull(c, False)
        cv2.drawContours(pesudo_mask, [hull], 0, 255, -1)
    
    result = cv2.bitwise_and(img, img, mask=pesudo_mask)
    if len(contours) != 0:
        # draw in blue the contours that were founded
        # cv2.drawContours(result, contours, -1, (255, 255, 0), 3)

        # find the biggest countour (c) by the area
        c = max(contours, key = cv2.contourArea)
        cv2.drawContours(result, [c], 0, (255, 125, 255), 3)
        cv2.drawContours(result, [hull], 0, (255, 0, 255), 3)
        x,y,w,h = cv2.boundingRect(c)

    # draw the biggest contour (c) in green
    cv2.rectangle(result,(x,y),(x+w,y+h),(255, 128, 128),2)
  
    return result, pesudo_mask, [x, y, w, h]


def ball_in_table_detect(img, mask, bg_mask):

    output = img.copy()
    ball_segment = mask - bg_mask
    contours, hierarchy = cv2.findContours(ball_segment, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    if len(contours) != 0:
        # find the biggest countour (c) by the area
        cv2.drawContours(output, contours, -1, (255, 255, 0), 3)
        c = max(contours, key = cv2.contourArea)
        cv2.drawContours(output, [c], 0, (255, 128, 128), -1)
        x,y,w,h = cv2.boundingRect(c)

    return output

def detect_ball_Houghtransform(img, mask):

    # Creating kernel
    kernel = np.ones((7, 7), np.uint8)

    output = img.copy()
    ball_segment = mask.copy()
    ball_segment = cv2.erode(ball_segment, kernel)

    detected_circles = cv2.HoughCircles(ball_segment, 
                   cv2.HOUGH_GRADIENT, 1, 50, param1 = 80,
               param2 = 10, minRadius = 1, maxRadius = 50)

    c = []
    if detected_circles is not None:
        # Convert the circle parameters a, b and r to integers.
        detected_circles = np.uint16(np.around(detected_circles))
    
        detected_circles = detected_circles[0, :]
        detected_circles = detected_circles[detected_circles[:, 2].argsort()]
        for pt in detected_circles:
            a, b, r = pt[0], pt[1], pt[2]
            # Draw the circumference of the circle.
            cv2.circle(output, (a, b), r, (255, 255, 0), -1)
        
      
        c = detected_circles[-1]
        cv2.circle(output, (c[0], c[1]), c[2], (0, 0, 255), -1)

    return output, c

def draw_trajectory(img, trajectory):
     
    output = img.copy()
    n = len(trajectory)
    if(n > 1):
        for i in range(max(0, n - 4), n - 1):
            a1, b1, r1 = trajectory[i]
            a2, b2, r2 = trajectory[i+1]
            cv2.circle(output, (a1, b1), 4, (255, 255, 255), -1)
            if(b2 > b1):
                cv2.line(output, (a1, b1), (a2, b2), (0, 255, 0), 2)
            else:
                cv2.line(output, (a1, b1), (a2, b2), (0, 165, 255), 2)
    return output



def draw_color_hist(img):
    b, g, r = cv2.split(img) #h s v
    fig = plt.figure()
    axis = fig.add_subplot(1, 1, 1, projection="3d")
    pixel_colors = img.reshape((np.shape(img)[0]*np.shape(img)[1], 3))
    norm = colors.Normalize(vmin=-1.,vmax=1.)
    norm.autoscale(pixel_colors)
    pixel_colors = norm(pixel_colors).tolist()
    axis.scatter(r.flatten(), g.flatten(), b.flatten(), facecolors=pixel_colors, marker=".")
    # axis.set_xlabel("Red")
    # axis.set_ylabel("Green")
    # axis.set_zlabel("Blue")
    axis.set_zlabel("Hue")
    axis.set_ylabel("Saturation")
    axis.set_xlabel("Value")
    plt.show()
    # plt.pause(0.1)

import os

if __name__ == "__main__":

    for video in os.listdir("video_data"):
        cap = cv2.VideoCapture(os.path.join('video_data', video))
        fps = cap.get(cv2.CAP_PROP_FPS)
        print("Video name: ", video)
        print("Frame rate: ", int(fps), "FPS")

        size = (640, 480)
        fourcc = cv2.VideoWriter_fourcc('X','V','I','D')
        # output = cv2.VideoWriter('half_table_middle.avi', fourcc, fps, size)
        output = cv2.VideoWriter(os.path.join('result_video', video + ".avi"), fourcc, 10, size)
        flag = 0
        trajectory = []
        try:
            while(cap.isOpened()):
                ret, frame = cap.read()
            
                re_frame = cv2.resize(frame, size, interpolation = cv2.INTER_AREA)
                out, mask, rec = detect_table_Color(re_frame)
                if(flag == 0):
                    mask_bg = mask
                    flag += 1
                table_with_ball, c = detect_ball_Houghtransform(out, mask)
                # draw_color_hist(out)
                if(len(c) > 0):
                    trajectory.append(c)
                    table_with_ball = draw_trajectory(table_with_ball, trajectory)
                else:
                    trajectory = []

                cv2.imshow('contours',  table_with_ball)
                cv2.imshow('frame', re_frame)
                #   cv2.waitKey(10)
                if cv2.waitKey(33) & 0xFF == ord('q'):
                    break
                output.write(table_with_ball)
        except:
            cap.release()
            cv2.destroyAllWindows()