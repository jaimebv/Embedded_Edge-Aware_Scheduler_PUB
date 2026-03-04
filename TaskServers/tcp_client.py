#!/usr/bin/env python

import socket
import time


TCP_IP = '192.168.1.100'
TCP_PORT = 6002
BUFFER_SIZE = 1024
MESSAGE = "Hello from Client! JB"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT)) #establishes the connection

while (1):
	s.send(bytes(MESSAGE,encoding='utf-8' ))#sends a message to the server
	#data = s.recv(BUFFER_SIZE) #waits for a reply from the Server
	
	#print ("received data:", data)
	# finish_connection = input("Finish connection (Y/N)")
	# if finish_connection== "Y":
	# 	s.send("close_connection")#sends a message to the server
	# 	break
	time.sleep(2)
s.close() #closes the socket