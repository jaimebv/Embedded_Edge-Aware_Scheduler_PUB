import argparse 
import cv2
import imutils

def GIMP_HSV_To_OpenCV_HSV(gimpH, gimpS, gimpV):
    '''
    This function converts the HSV values of a color as seen in GIMP to OpenCV HSV form.
    References: https://gist.github.com/akashjobanputra/fd90aa23ca22b703bad6886f3e9a7d24
    '''
    opencvH = float(gimpH / 2)
    opencvS = float(gimpS / 100) * 255
    opencvV = float(gimpV / 100) * 255

    return (opencvH, opencvS, opencvV)




def OpenCV_HSV_To_HSV(opencvH, opencvS, opencvV):
    '''
    This function converts the HSV values of a color as seen in GIMP to OpenCV HSV form.
    References: https://gist.github.com/akashjobanputra/fd90aa23ca22b703bad6886f3e9a7d24
    '''
    H= float(opencvH * 2)
    S= float(opencvS * 100) / 255
    V= float(opencvV * 100) / 255

    return (H, S, V)


#print(GIMP_HSV_To_OpenCV_HSV(21,100, 55))
print(OpenCV_HSV_To_HSV(160.0, 123.0, 153.0))
print(OpenCV_HSV_To_HSV(180.0, 255.0, 255.0))
print(OpenCV_HSV_To_HSV(0.0, 150.0, 150.0))
print(OpenCV_HSV_To_HSV(15.0, 255.0, 255.0))


print (GIMP_HSV_To_OpenCV_HSV(360, 100, 100))
print (GIMP_HSV_To_OpenCV_HSV(14, 93, 71))

# low_apple_red = (160.0, 123.0, 153.0)
# high_apple_red = (180.0, 255.0, 255.0)
# low_apple_raw = (0.0, 150.0, 150.0)
# high_apple_raw = (15.0, 255.0, 255.0)