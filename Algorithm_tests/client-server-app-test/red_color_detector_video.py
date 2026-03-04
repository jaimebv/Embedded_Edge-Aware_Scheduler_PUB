import argparse 
import cv2
import imutils

# Defining the color ranges to be filtered.
# The following ranges should be used on HSV domain image.
low_apple_red = (160.0, 153.0, 153.0)
high_apple_red = (180.0, 255.0, 255.0)
low_apple_raw = (0.0, 150.0, 150.0)
high_apple_raw = (15.0, 255.0, 255.0)



# ap = argparse.ArgumentParser()
# ap.add_argument("-i","--image", required=True, help="Path to input image")
# args = vars(ap.parse_args())

#image_bgr = cv2.imread("apple.jpg")





cam = cv2.VideoCapture(0)

img_counter = 0



while True:
    ret, image_bgr = cam.read()
    #image_bgr = cv2.imread("apple.jpg")  
    # image_bgr = imutils.resize(image_bgr, width=320)

    # image_bgr = cv2.flip(image_bgr,180)
    
    image = image_bgr.copy()
    #image_hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    image_hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    mask_red = cv2.inRange(image_hsv,low_apple_red, high_apple_red)
    mask_raw = cv2.inRange(image_hsv,low_apple_raw, high_apple_raw)

    mask = mask_red + mask_raw
    cv2.circle(image_hsv, (150, 150), 20, low_apple_red, 2)
    cv2.circle(image_hsv, (250, 250), 20, high_apple_red, 2)
    cnts,_ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)
    c_num=0
    for i,c in enumerate(cnts):
        # draw a circle enclosing the object
        ((x, y), r) = cv2.minEnclosingCircle(c)
        if r>34:
            c_num+=1
            cv2.circle(image, (int(x), int(y)), int(r), (0, 255, 0), 2)
            cv2.putText(image, "#{}".format(c_num), (int(x) - 10, int(y)), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        else:
            continue










    
    cv2.imshow('deteted',image)
    cv2.imshow("HSV image", image_hsv)    
    cv2.imshow("Mask image", mask)
        
    img_counter += 1


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    

cam.release()