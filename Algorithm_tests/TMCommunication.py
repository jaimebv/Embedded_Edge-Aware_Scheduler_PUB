#TMCommunication.py

#:::DESCRIPTION:::
#This script is used to handle all communications between TaskMonitor component
#and any other component. It allows to easily select the communication protocol/method
#[OOP,REST, etc...]. thus, it implements certain algorithm based on the communication method selected
#Applies polymorphism so whenever we want to communicate with any component from SchedulerInterface, we send the 
#communication object, the protocol and the function name
#Example1: TMCommunication.communicate (self.myTMDMComm, "OOP", "send parameters")
#implements the send_:parameters function through the OOP communication method between TaskMonitor component
#and DecisionMaker Component

#TMCommunication defines the following classes:
#   *TaskMonitorDecisionMakerCommunication: implements all communication functions between TaskMonitor component
#     and DecisionMaker Component

#from DesicionMaker import TaskMonitorAPI
import requests #To implement REST feature
import json


class TaskMonitorDesicionMakerCommunication():
    def __init__(self) -> None:
        pass

    def communicate (self, protocol, function, **kwargs):

        if protocol=="OOP":
            #myDMComm=TaskMonitorAPI()
            #function "set issues"
            if function == "set issues":
                pass 
            else:
                pass
            
        elif protocol=="REST":
            #function "set issues"
            if function == "set issues":
                headers = {'Content-type': 'application/json', 'Accept': '*/*'}
                response_gotten = requests.post("http://127.0.0.1:5000/dm/tm/latest_issues", data=json.dumps(kwargs["_parameters_"]),headers=headers)
                response_json=response_gotten.json()
                response=response_json

            else:
                pass

        elif protocol=="SocketTCP":
            #function "set issues"
            if function == "set issues":
                pass
            else:
                pass
        elif protocol=="SocketUDP":
            #function "set issues"
            if function == "set issues":
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