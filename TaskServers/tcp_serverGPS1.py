import socket   
import time       
import json 
import random 
 
# next create a socket object
s = socket.socket()        
print ("Socket successfully created")
 
# reserve a port on your computer in our
# case it is 12345 but it can be anything
port = 5005             
 
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



def generateCoordinates(lat, lon):
  pos_lat=random.randint(0,1)
  pos_lon=random.randint(0,1)
  coordinates={}

  if pos_lat== 1:
    lat_x=lat+ random.random()
  else:
    lat_x=lat- random.random()
  if pos_lon== 1:
    lon_x=lon+ random.random()
  else:
    lon_x=lon- random.random()
  
  coordinates["Lat"]=lat_x
  coordinates["Lon"]=lon_x

  return str(coordinates)

{'Lat':2.00,'Lon':-70.00}
  





# a forever loop until we interrupt it or
# an error occurs
while True:
 
# Establish connection with client.
  #time.sleep(2)
  c, addr = s.accept()    
  print ('Got connection from', addr )
  data = c.recv(2048)
  print(data)
  res = eval(data.decode())
  print(res)

  cars_near= random.randint(0, 9)

  cars_dict={}
  for car_number in range (cars_near):
    cars_dict[car_number]=generateCoordinates(res["Lat"],res["Lon"])


  # send a thank you message to the client. encoding to send byte type.
  #time.sleep(2)
  
  message=str(cars_dict)+'*'
  print(message)
  c.send(message.encode())
 
  # Close the connection with the client
  c.close()
   
  # Breaking once connection closed
  #break