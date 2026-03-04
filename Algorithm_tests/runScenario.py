import os                                                                       
import threading 
import time
import DesicionMaker
import DummyDesicionMaker    
import TaskMonitor
import ECM                                    
import socket   
import requests
import json   
from PesDBManager import PESDBManager
from SupplicantDBManager import SupplicantDBManager       
from datetime import datetime, timedelta                                                      
import cv2
import numpy as np
                                                                                

COMPUTER_IP="192.168.1.100"
ESP_IP="192.168.1.101"



now = datetime.now() #get the time when the script is executed
now=str(now.strftime("%d-%m-%Y-%H_%M_%S")) #formats the time
now=now.replace(" ", "_")
now=now.replace(":", "_")
now=now.replace(".", "_") #replaces chars for formatting

dirname, filename = os.path.split(os.path.abspath(__file__))
log_path=str(dirname) #creates a log file with this base path
filename_data_log= log_path+"/LOGS/ScenarioTimes_"+str(now)+".log"
print(filename_data_log)

continue_server_flag=True # flag used to stop the server globally                                       
time_sleep_tcp_picture=0
continue_server_flag_tcp=True

#Name:clearDBs
#Clears both data bases pes_registry and supplicant_registry
#Parameters: None
#return: None
def clearDBs ():
    dirname, filename = os.path.split(os.path.abspath(__file__))
    db_path=str(dirname)+ "\\pes_registry.db"
    print ("database path is: ", db_path)
    myPESmanager=PESDBManager(db_path) #creates an object to manage Pes_registry db
    myPESmanager.clear_pes_table() #clears all registries to have a fresh start
    myPESmanager.close_connection()

    dirname, filename = os.path.split(os.path.abspath(__file__))
    db_path=str(dirname)+ "\\supplicant_registry.db"
    print ("database path is: ", db_path)
    mysupplicantmanager=SupplicantDBManager(db_path)  #creates an object to manage supplicant_registry db
    mysupplicantmanager.clear_supplicants_table() #clears all registries to have a fresh start
    mysupplicantmanager.close_connection()

#Name:runTCPServer
#Method used to create a TCP server as a thread
#Parameters: Port[int] of the TCP server
#return: None
def runTCPServer(port):
    global continue_server_flag_tcp
    global time_sleep_tcp
    s = socket.socket()        
    print ("Socket successfully created")
                
    
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
    while continue_server_flag_tcp:
        
        # Establish connection with client.
        #time.sleep(2)
        c, addr = s.accept()    
        print ('Got connection from', addr )
        data = c.recv(2048)
        print(data)
        # send a thank you message to the client. encoding to send byte type.
        time.sleep(time_sleep_tcp_picture)
        c.send('Thank you for connecting*'.encode())
        
        # Close the connection with the client
        c.close()
        
        # Breaking once connection closed
        #break

    print ("server closed")



#Name:runTCPServerPicture
#Method used to create a TCP server as a thread
#Parameters: Port[int] of the TCP server
#return: None
def runTCPServerPicture(port):
    global continue_server_flag
    global time_sleep_tcp_picture
    s = socket.socket()        
    print ("Socket successfully created")
    
    # reserve a port on your computer in our
    #port = 6002              
    
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

    while continue_server_flag:
        
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
            
        
        #cv2.imshow('img', image)
        #cv2.waitKey(1)
        # send a thank you message to the client. encoding to send byte type.
        MESSAGE = "Faces: " + str(len(faces)) +"*"
        time.sleep(time_sleep_tcp_picture)
        c.send(MESSAGE.encode())
        print("+++++++++++++++++++++++++++++++",MESSAGE)
        
        # Close the connection with the client
        c.close()
        
        # Breaking once connection closed
        #break









#Name:migrateTask
#Method used to create a TCP server as a thread
#Parameters: 
# _task_id_ -> [str] task id as in the embedded device
#  _ip_ -> [str] IP of the new edge-server within the network after match-making
# _port_ ->[int] Port of the new edge-server within the network after match-making
#return: None
def migrateTask(_task_id_, _ip_, _port_):

    headers = {'Content-type': 'application/json', 'Accept': '*/*'}
    message={"task_id":_task_id_,"pes":_ip_,"port":_port_}
    URL="http://"+ESP_IP+":80/pes-update/"
    response_gotten = requests.post(URL, data=json.dumps(message),headers=headers)
    print ("+++++++++++++++++",response_gotten)

#Name:resumeTask
#Method used to send a resume task request to the embedded device
#Parameters: 
# _task_id_ -> [str] task id as in the embedded device
#  _type_ -> [str] the type of the task (client/server)
#return: None
def resumeTask(_task_id_,_type_):
    headers = {'Content-type': 'application/json', 'Accept': '*/*'}
    message={"task_id":_task_id_,"type":_type_}
    URL="http://"+ESP_IP+":80/resume-task/"
    response_gotten = requests.post(URL, data=json.dumps(message),headers=headers)
    print ("+++++++++++++++++",response_gotten)

#Name:suspendTask
#Method used to send a suspend task request to the embedded device
#Parameters: 
# _task_id_ -> [str] task id as in the embedded device
#  _type_ -> [str] the type of the task (client/server)
#return: None
def suspendTask(_task_id_,_type_):
    URL="http://"+ESP_IP+":80/suspend-task/"
    response_gotten = requests.delete(URL+_task_id_+"_"+ _type_)
    print ("+++++++++++++++++",response_gotten)


#Name:registerNode
#Method used to register a new node in ENIM through its API
#Parameters: 
# _node_id_ -> [str] name of the node
#  _ip_ -> [str] IP of the node within the network
#return: None
def registerNode(_node_id_,_ip_=COMPUTER_IP,PORT=6002):
    
    message={
    "id" : "node2",
    "ipAddress": _ip_+":"+ str(PORT),
    "connected" : True,
    "totalResource" : 2000000,
    "totalNetwork" : 2000000,
    "location" : 8,
    "heartBeatInterval" : 1500000
    }
    
    headers = {'Content-type': 'text/plain', 'Accept': '*/*'}
    response_gotten = requests.post("http://127.0.0.1:4567/rest/node/register", data=json.dumps(message),headers=headers)
    print ("+++++++++++++++++",response_gotten)


#Name:register_client
#Registers a certain client with ENIM
#Parameters: 
# client_id[str] -> a name for the client to register with ENIM
# RE2EL[int] -> Requested End-to-End Latency
# location[int] -> Location of the UE. Currently only this parameter is used for match-making
#return: None
def register_client(client_id="client1", RE2EL=5,location=5):

    client_to_register = {
        "id": client_id,
        "reqNetwork": 1,
        "reqResource": 1,
        "location": location,
        "heartBeatInterval": 15000000000
    }
  
    headers = {'Content-type': 'text/plain', 'Accept': '*/*'}
    register_response = requests.post("http://127.0.0.1:4567/rest/client/register", data=json.dumps(client_to_register),headers=headers)
    
    return register_response


#Name:addMinute
#Add one minute to the time given as argument
#Parameters: 
# date_time[datetime] -> time to which sum 1 minute
#return: None
def addMinute(date_time):
    date_time=date_time + timedelta(minutes=1)
    return date_time


#Name:addMinute
#Add one minute to the time given as argument
#Parameters: 
# date_time[datetime] -> time to which sum x minutes
#return: None
def addMinutes(date_time, x):
    date_time=date_time + timedelta(minutes=x)
    return date_time



def Scenario1():
    global continue_server_flag
    clearDBs() #clean up all registries before start
    suspendTask(_task_id_="t2",_type_="client") #make sure t2 is suspended
    time.sleep(1)

    suspendTask(_task_id_="t3",_type_="client") #make sure t3 is suspended
    print("t2 and t3 suspended")
    time.sleep(1)

    resumeTask(_task_id_="t2",_type_="client") #make sure t2 is resumed
    print("t2 resumed... starting in 20sec")
    time.sleep(20)

    print("******************START*******************")
    t = threading.Thread(target=runTCPServerPicture, args=(6003,)) #create a TCP server running at port 6003
    t.daemon= True
    t.start()
    time.sleep(1)

    suspendTask(_task_id_="t3",_type_="client") #make sure t3 is suspended (again)
    print("t3 suspended")
    time.sleep(1)

    migrateTask(_task_id_="t1", _ip_=COMPUTER_IP, _port_=6003)
    print("t1 migrated to port 6003 to have a timeout")
    time.sleep(5)

    #******************************* CREATE INDIVIDUAL THREADS FOR EEAS COMPONENTS *******************************
    # *************************************
    #create an object of the ECM component and run it as a thread
    objECM=ECM.ECMEngine()
    t7= threading.Thread(target=lambda: ECM.app.run(port=5001, debug=True, use_reloader=False))
    t7.daemon= True
    t7.start()
    # *************************************
    #create an object of the DM component and run all threads
    obj=DesicionMaker.DecisionMakerEngine()#sets _issues_data to default param to get the system started
    obj.myECMAPI.cancel_active_supplicants_to_start() #Makes sure any supplicant that might have conserved a "IN_PROGRESS" is canceled

    t = threading.Thread(target=obj.apply_decision_methodology, args=())
    t.daemon= True
    t.start()

    t2 = threading.Thread(target=obj.ECM_listener, args=())
    t2.daemon= True
    t2.start()

    t3= threading.Thread(target=lambda: DesicionMaker.app.run(port=5000, debug=True, use_reloader=False))
    t3.daemon= True
    t3.start()

    # *************************************
    #create an object of the TM component and run all threads
    objTM=TaskMonitor.TaskMonitorEngine()

    #this thread will be constantly listening any incoming response from SI
    # NOTE: It modifies the value of supplicant_registry (TODO: mutex)
    t4 = threading.Thread(target=objTM.TM_listener, args=())
    t4.daemon= True
    t4.start()
    
    #this thread runs the REST server of TM Component
    t5= threading.Thread(target=lambda: TaskMonitor.app.run(host="0.0.0.0", port=4999, debug=True, use_reloader=False))
    t5.daemon= True
    t5.start()


    t6 = threading.Thread(target=objTM.TI_listener, args=())
    t6.daemon= True
    t6.start()
    time.sleep(1)

    times={} #creates an empty dictionary to store start and end time
#-->starting point
    x_start=datetime.now()
    x_end=addMinute(x_start)
    times["start"]=str(x_start)
    times["end"]=str(x_end)

    #writes the start and end time into a logfile
    f = open(filename_data_log, "w")
    f.write(str(times))
    f.close()

    time.sleep(10)
    #After 10 seconds stop the TCP server so the task starts to have a TIMEOUT and EEAS reacts
    continue_server_flag=False

    #After 30 seconds register a new server to ENIM
    #Make sure you have this server already running separately before running the scenario
    time.sleep(30)

    # t = threading.Thread(target=runTCPServer, args=(6002,))
    # t.daemon= True
    # t.start()

    print("\n\n\n\n\n\n\n\n")
    print("REGISTERING NEW NODE\n\n")
    registerNode("node2",COMPUTER_IP)
    #register_client()
    #Give 20 seconds to migrate to the new server
    time.sleep(20)

#-->end point


    time.sleep(2)




def Scenario2():
    clearDBs() #clean up all registries before start
    print("starting in 10sec")
    time.sleep(10)

    print("******************START*******************")
    # t = threading.Thread(target=runTCPServerPicture, args=(6003,)) #create a TCP server running at port 6003
    # t.daemon= True
    # t.start()
    # time.sleep(1)

    # migrateTask(_task_id_="t1", _ip_=COMPUTER_IP, _port_=6003)
    # print("t1 migrated to port 6003")
    # time.sleep(5)

    #******************************* CREATE INDIVIDUAL THREADS FOR EEAS COMPONENTS *******************************
    # *************************************
    #create an object of the ECM component and run it as a thread
    objECM=ECM.ECMEngine()
    t7= threading.Thread(target=lambda: ECM.app.run(port=5001, debug=False, use_reloader=False))
    t7.daemon= True
    t7.start()
    # *************************************
    #create an object of the DM component and run all threads
    obj=DummyDesicionMaker.DecisionMakerEngine()#sets _issues_data to default param to get the system started
    obj.myECMAPI.cancel_active_supplicants_to_start() #Makes sure any supplicant that might have conserved a "IN_PROGRESS" is canceled

    # t = threading.Thread(target=obj.apply_decision_methodology, args=())
    # t.daemon= True
    # t.start()

    # t2 = threading.Thread(target=obj.ECM_listener, args=())
    # t2.daemon= True
    # t2.start()

    t3= threading.Thread(target=lambda: DummyDesicionMaker.app.run(port=5000, debug=False, use_reloader=False))
    t3.daemon= True
    t3.start()

    # *************************************
    #create an object of the TM component and run all threads
    objTM=TaskMonitor.TaskMonitorEngine()

    #this thread will be constantly listening any incoming response from SI
    # NOTE: It modifies the value of supplicant_registry (TODO: mutex)
    t4 = threading.Thread(target=objTM.TM_listener, args=())
    t4.daemon= True
    t4.start()
    
    #this thread runs the REST server of TM Component
    t5= threading.Thread(target=lambda: TaskMonitor.app.run(host="0.0.0.0", port=4999, debug=False, use_reloader=False))
    t5.daemon= True
    t5.start()

    t6 = threading.Thread(target=objTM.TI_listener, args=())
    t6.daemon= True
    t6.start()
    time.sleep(1)

    times={} #creates an empty dictionary to store start and end time
#-->starting point
    x_start=datetime.now()
    x_end=addMinutes(x_start,10)
    times["start"]=str(x_start)
    times["end"]=str(x_end)

    #writes the start and end time into a logfile
    f = open(filename_data_log, "w")
    f.write(str(times))
    f.close()

    time.sleep(600)

#-->end point

    time.sleep(2)





def Scenario3():
    global time_sleep_tcp_picture
    clearDBs() #clean up all registries before start
    print("starting in 10sec")
    time.sleep(10)

    print("******************START*******************")
    t = threading.Thread(target=runTCPServer, args=(5005,)) #create a TCP server running at port 5005
    t.daemon= True
    t.start()
    time.sleep(1)

    #migrateTask(_task_id_="t1", _ip_=COMPUTER_IP, _port_=5005)
    print("t1 migrated to port 5005")
    time.sleep(5)

    # #******************************* CREATE INDIVIDUAL THREADS FOR EEAS COMPONENTS *******************************
    # # *************************************
    # #create an object of the ECM component and run it as a thread
    # objECM=ECM.ECMEngine()
    # t7= threading.Thread(target=lambda: ECM.app.run(port=500, debug=False, use_reloader=False))
    # t7.daemon= True
    # t7.start()
    # # *************************************
    # #create an object of the DM component and run all threads
    # obj=DummyDesicionMaker.DecisionMakerEngine()#sets _issues_data to default param to get the system started
    # obj.myECMAPI.cancel_active_supplicants_to_start() #Makes sure any supplicant that might have conserved a "IN_PROGRESS" is canceled

    # t = threading.Thread(target=obj.apply_decision_methodology, args=())
    # t.daemon= True
    # t.start()

    # t2 = threading.Thread(target=obj.ECM_listener, args=())
    # t2.daemon= True
    # t2.start()

    # t3= threading.Thread(target=lambda: DummyDesicionMaker.app.run(port=5000, debug=False, use_reloader=False))
    # t3.daemon= True
    # t3.start()

    # # *************************************
    # #create an object of the TM component and run all threads
    # objTM=TaskMonitor.TaskMonitorEngine()

    # #this thread will be constantly listening any incoming response from SI
    # # NOTE: It modifies the value of supplicant_registry (TODO: mutex)
    # t4 = threading.Thread(target=objTM.TM_listener, args=())
    # t4.daemon= True
    # t4.start()
    
    # #this thread runs the REST server of TM Component
    # t5= threading.Thread(target=lambda: TaskMonitor.app.run(host="0.0.0.0", port=4999, debug=False, use_reloader=False))
    # t5.daemon= True
    # t5.start()

    # t6 = threading.Thread(target=objTM.TI_listener, args=())
    # t6.daemon= True
    # t6.start()
    # time.sleep(1)

    times={} #creates an empty dictionary to store start and end time
#-->starting point
    x_start=datetime.now()
    x_end=addMinutes(x_start,1)
    times["start"]=str(x_start)
    times["end"]=str(x_end)

    #writes the start and end time into a logfile
    f = open(filename_data_log, "w")
    f.write(str(times))
    f.close()
    # registerNode("node3",COMPUTER_IP,5006)
    time.sleep(10)
    print("\n\n\n\nchange latency\n\n\n")
    time_sleep_tcp_picture=0.3 #simulating an Oe2el degradation
    time.sleep(10)


    time.sleep(40)

#-->end point

    time.sleep(2)   





if __name__ == '__main__':

    Scenario2()
    #Scenario3()