# #!/usr/bin/env python
# #first run the server which listenes to the clients
# import socket
# import sys
# import threading

# host = ''
# port = 6001
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# try:
#     s.bind((host, port))
# except socket.error as e:
#     print(str(e))

# s.listen(5)
# print('Waiting for a connection.')
# def threaded_client(conn,address, port):
#     conn.send(str.encode('Welcome, type your info\n'))
# #receive name of the car
#     while True:
#         print ("hearth beat from server on: "+ str(port))
#         data = conn.recv(2048)
#         reply = data
#         print (data)
#         conn.sendall(reply)
#     #conn.close()
    


# while True:

#     conn, addr = s.accept()
#     print('connected to: '+addr[0]+':'+str(addr[1]))
# #function to determine if there is new data "peak"
# #start_new_thread(threaded_client,(conn,))
#     try:
#         t = threading.Thread(target=threaded_client, args=(conn,addr[0],addr[1]))
#         t.daemon= True
#         t.start()
#         #thread.start_new_thread(threaded_client,(conn,))

#     except Exception as errtxt:
#         print (errtxt)
    
		









		
# #thread to location speed, etc
# #thread for login

# first of all import the socket library
import socket            
 
# next create a socket object
s = socket.socket()        
print ("Socket successfully created")
 
# reserve a port on your computer in our
# case it is 12345 but it can be anything
port = 6002              
 
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
 
# a forever loop until we interrupt it or
# an error occurs
while True:
 
# Establish connection with client.
  c, addr = s.accept()    
  print ('Got connection from', addr )
  data = c.recv(2048)
  print(data)
  # send a thank you message to the client. encoding to send byte type.
  c.send('Thank you for connecting'.encode())
 
  # Close the connection with the client
  c.close()
   
  # Breaking once connection closed
  #break