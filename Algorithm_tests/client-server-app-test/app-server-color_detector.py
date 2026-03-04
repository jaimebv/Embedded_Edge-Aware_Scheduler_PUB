# Import the required modules
from IPython.display import clear_output
import socket
import sys
import cv2
import matplotlib.pyplot as plt
import pickle
import numpy as np
import struct ## new
import zlib
from PIL import Image, ImageOps

HOST=''
PORT=8485

# Defining the color ranges to be filtered.
# The following ranges should be used on HSV domain image.
low_apple_red = (160.0, 153.0, 153.0)
high_apple_red = (180.0, 255.0, 255.0)
low_apple_raw = (0.0, 150.0, 150.0)
high_apple_raw = (15.0, 255.0, 255.0)
blob_trheshold=20
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
print('Socket created')

s.bind((HOST,PORT))
print('Socket bind complete')
s.listen(10)
print('Socket now listening')

conn,addr=s.accept()

data = b""
payload_size = struct.calcsize(">L")
print("payload_size: {}".format(payload_size))
while True:
    while len(data) < payload_size:
        data += conn.recv(4096)
    # receive image row data form client socket
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack(">L", packed_msg_size)[0]
    while len(data) < msg_size:
        data += conn.recv(4096)
    frame_data = data[:msg_size]
    data = data[msg_size:]
    # unpack image using pickle 
    frame=pickle.loads(frame_data, fix_imports=True, encoding="bytes")
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)


    image = frame.copy()



    image_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    mask_red = cv2.inRange(image_hsv,low_apple_red, high_apple_red)
    mask_raw = cv2.inRange(image_hsv,low_apple_raw, high_apple_raw)

    mask = mask_red + mask_raw
    #cv2.circle(image_hsv, (150, 150), 20, low_apple_red, 2)
    #cv2.circle(image_hsv, (250, 250), 20, high_apple_red, 2)
    cnts,_ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)
    c_num=0
    for i,c in enumerate(cnts):
        # draw a circle enclosing the object
        ((x, y), r) = cv2.minEnclosingCircle(c)
        if r>blob_trheshold:
            c_num+=1
            cv2.circle(image, (int(x), int(y)), int(r), (0, 255, 0), 2)
            cv2.putText(image, "#{}".format(c_num), (int(x) - 10, int(y)), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        else:
            continue










    
    cv2.imshow('APP SERVER: Deteted image ',image)
    #cv2.imshow("HSV image", image_hsv)    
    cv2.imshow("APP SERVER: Mask image", mask)
        
    


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    

