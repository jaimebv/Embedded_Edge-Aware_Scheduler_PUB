# /*
#  *  SW for receiving images from the Kaluga V1.3 board as a TCP bytes buffer and converting it 
#  *  into a cv2 image. This is only a test and cannot be used in production.
#  *  
#  *  KNOWN BUGS:
#  *  The system is not perfectly synch, thus it presents some issues wheren woring faster than 100ms
#  *  per loop. It falls into a deadlock where both client (this) and server wait for an ACK
#  *  this happens due to a packet arriving together with other in the client (2 consecutives ACK)
#  *  
#  *  HOW TO USE:
#  *  1) Update the IP adress and port
#  *  2) Run the script
#  * 
#  *  Copyright (C) 2023 IERSE Universidad del Azuay (Cuenca - Ecuador).
#  *  http://www.uazuay.edu.ec
#  *
#  *  This program is free software: you can redistribute it and/or modify
#  *  it under the terms of the GNU Lesser General Public License as published by
#  *  the Free Software Foundation, either version 2.1 of the License, or
#  *  (at your option) any later version.

#  *  This program is distributed in the hope that it will be useful,
#  *  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  *  GNU Lesser General Public License for more details.

#  *  You should have received a copy of the GNU Lesser General Public License
#  *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  *
#  *  Version:		1.0
#  *  Design:			Jaime Burbano
#  *  Implementation: Jaime Burbano
#  */
import socket  
import cv2
import numpy as np

          
 
# next create a socket object
s = socket.socket()        
print ("Socket successfully created")
 
# reserve a port on your computer in our
port = 6003              
 
# Next bind to the port
# we have not typed any ip in the ip field
# instead we have inputted an empty string
# this makes the server listen to requests
# coming from other computers on the network
s.bind(('', port))        
print ("socket binded to %s" %(port))
 
# put the socket into listening mode
s.listen(5)    
print ("socket is listening")           
 
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

while True:
 
# Establish connection with client.
  c, addr = s.accept()    
  print ('Got connection from', addr )
  frame_data = c.recv(8192)
  #print(frame_data)
  image = np.asarray(bytearray(frame_data), dtype="uint8") #convert into an array
  image = cv2.imdecode(image, cv2.IMREAD_COLOR)   #decode the array into an cv2 image
    
  #cv2.imwrite("result.jpg", image) #case you want to store the image as a file
  #cv2.imshow('frames',image) #case you want to see the frames live
  gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  # Detect the faces
  
  faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    # Draw the rectangle around each face
  for (x, y, w, h) in faces:
        cv2.rectangle(image, (x, y), (x+w, y+h), (255, 0, 0), 2)
    # Display
     
  
  cv2.imshow('img', image)
  cv2.waitKey(1)
  # send a thank you message to the client. encoding to send byte type.
  MESSAGE = "Faces: " + str(len(faces)) +"*"
  c.send(MESSAGE.encode())
 
  # Close the connection with the client
  c.close()
   
  # Breaking once connection closed
  #break