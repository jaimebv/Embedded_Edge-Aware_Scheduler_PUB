#SICommunication.py

#:::DESCRIPTION:::
#This script is used to handle all communications between SchedulerInterface component
#and any other component. It allows to easily select the communication protocol/method
#[OOP,REST, etc...]. thus, it implements certain algorithm based on the communication method selected
#Applies polymorphism so whenever we want to communicate with any component from SchedulerInterface, we send the 
#communication object, the protocol and the function name
#Example1: SICommunication.communicate (self.mySITMComm, "OOP", "send parameters")
#implements the send_:parameters function through the OOP communication method between SchedulerInterface component
#and TaskMonitor Component

#SICommunication defines the following classes:
#   *SchedulerInterfaceTaskMonitorCommunication: implements all communication functions between SchedulerInterface component
#     and TaskMonitor Component

from TaskMonitor import TaskMonitor
import requests #To implement REST feature
import json


class SchedulerInterfaceTaskMonitorCommunication():
    def __init__(self) -> None:
        pass

    def communicate (self, protocol, function, **kwargs):

        if protocol=="OOP":
            myTMComm=TaskMonitor()
            #function "set parameters"
            if function == "set parameters":
                
                response= myTMComm.set_parameters(kwargs["_parameters_"])  
            else:
                pass
            
        elif protocol=="REST":
            #function "set parameters"
            if function == "set parameters":
                print ("*********", kwargs["_parameters_"])
                headers = {'Content-type': 'application/json', 'Accept': '*/*'}
                response_gotten = requests.post("http://127.0.0.1:4999/tm/si/latest_data", data=json.dumps(kwargs["_parameters_"]),headers=headers)
                response_json=response_gotten.json()
                response=response_json

            else:
                pass

        elif protocol=="SocketTCP":
            #function "set parameters"
            if function == "set parameters":
                pass
            else:
                pass
        elif protocol=="SocketUDP":
            #function "set parameters"
            if function == "set parameters":
                pass
            else:
                pass                        
        else:
            pass


        return response


#Name:communicate
#applies polymorphism so whenever we want to communicate with any component, we send the 
#communication object, the protocol and the function as generic paramentes
#Parameters: object [object], protocol [str], function[str]
 #return: specific communicate method based on object type

def communicate (object, protocol, function, **kwargs):

    return object.communicate(protocol, function, **kwargs)