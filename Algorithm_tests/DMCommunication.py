#DMCommunication.py

#:::DESCRIPTION:::
#This script is used to handle all communications between DecisionMaker component
#and any other component. It allows to easily select the communication protocol/method
#[OOP,REST, etc...]. thus, it implements certain algorithm based on the communication method selected
#Applies polymorphism so whenever we want to communicate with any component from DecisionMaker, we send the 
#communication object, the protocol and the function name
#Example1: DMCommunication.communicate (self.myDMTMComm, "OOP", "get issues")
#implements the get issues function through the OOP communication method between DecisionMaker component
#and TaskMonitor Component

#DMCommunication defines the following classes:
#   *DecisionMakerTaskMonitorCommunication: implements all communication functions between DecisionMaker component
#     and TaskMonitor Component
#   *DecisionMakerECMCommunication:implements all communication functions between DecisionMaker component
#     and ECM Component
#   *DecisionMakerSchedulerInterfaceCommunication:implements all communication functions between DecisionMaker component
#     and SchedulerInterface Component
#   *DecisionMakerTaskInterfaceCommunication:implements all communication functions between DecisionMaker component
#     and TaskInterface Component
import os
import logging
#from TaskMonitor import TaskMonitor
from ECM import ECMEngine
from SystemConfigurations import DecisionMakerConfig 
from SystemConfigurations import EmbeddedDeviceConfig 
import requests #To implement REST feature
import json

dirname, filename = os.path.split(os.path.abspath(__file__))
log_path=str(dirname)
filename_log= log_path+"/LOGS/DMCOMM.log"

# create logger
loggerDMCOMM = logging.getLogger('DM-COMMUNICATION')
loggerDMCOMM.setLevel(logging.DEBUG)
# create console handler and set level to debug
chDMCOMM = logging.FileHandler(filename_log, mode='w')
chDMCOMM.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to chDMCOMM
chDMCOMM.setFormatter(formatter)
# add chDMCOMM to logger
loggerDMCOMM.addHandler(chDMCOMM)




class DecisionMakerTaskMonitorCommunication():

    DMConfig=DecisionMakerConfig()

    def __init__(self) -> None:

        pass

    def communicate (self, protocol, function, **kwargs):

        if protocol=="OOP":
            pass
            # myTMComm=TaskMonitor()

            # #function "get issues"
            # if function == self.DMConfig.DMTMcommunication_functions[0]:               
            #     response= myTMComm.get_issues()  
            # #function "clean issues"
            # elif function == self.DMConfig.DMTMcommunication_functions[1]:               
            #     response= myTMComm.clean_issue_flag_list()
            # else:
            #     loggerDMCOMM.error ("COMMUNICATION DM: communication function not found")

        elif protocol=="REST":
            #function "get issues"
            response="NULL"
            if function == self.DMConfig.DMTMcommunication_functions[0]:
                response_gotten = requests.get("http://127.0.0.1:5000/dm/tm/latest_issues")
                
                response_json=response_gotten.json()
                response=response_json 
                         
            #function "clean issues"
            elif function == self.DMConfig.DMTMcommunication_functions[1]:
                pass
            #function "set issues"
            elif function == self.DMConfig.DMTMcommunication_functions[2]:
                headers = {'Content-type': 'application/json', 'Accept': '*/*'}
                response_gotten = requests.post("http://127.0.0.1:5000/dm/tm/latest_issues", data=json.dumps(kwargs["_data_"]),headers=headers)
                response_json=response_gotten.json()
                response=response_json
            
            else:
               loggerDMCOMM.error ("COMMUNICATION DM: " + str(function) + " communication function not found")

        elif protocol=="SocketTCP":

            #function "get issues"
            if function == self.DMConfig.DMTMcommunication_functions[0]:
                pass
            #function "clean issues"
            elif function == self.DMConfig.DMTMcommunication_functions[1]:
                pass
            else:
                loggerDMCOMM.error ("COMMUNICATION DM: communication function not found")

        elif protocol=="SocketUDP":

            #function "get issues"
            if function == self.DMConfig.DMTMcommunication_functions[0]:
                pass
            #function "clean issues"
            elif function == self.DMConfig.DMTMcommunication_functions[1]:
                pass
            else:
                loggerDMCOMM.error ("COMMUNICATION DM: communication function not found")  

        else:
            loggerDMCOMM.error ("COMMUNICATION DM:communication protocol not found")


        return response




class DecisionMakerECMCommunication():

    DMConfig=DecisionMakerConfig()

    def __init__(self) -> None:

        pass



    def communicate (self, protocol, function, **kwargs):

        response=0

        if protocol=="OOP":
            myECMComm=ECMEngine()

            #function "open supplicant"
            if function == self.DMConfig.DMECMcommunication_functions[0]:
                response= myECMComm.open_supplicant(kwargs["_ask_times_"] ,kwargs["_hold_time_"] ,kwargs["_RE2EL_"] ,kwargs["_supplicant_id_"] , kwargs["_task_id_"],kwargs["_OE2EL_"] )  
            #function "cancel supplicant"
            elif function == self.DMConfig.DMECMcommunication_functions[1]:
                response= myECMComm.cancel_supplicant(kwargs["_supplicant_id_"]  )  
            #function "get related supplicant"
            elif function == self.DMConfig.DMECMcommunication_functions[2]:
                response= myECMComm.get_supplicant(kwargs["_task_id_"],kwargs["_policy_name_"])  
            #function "get supplicant by id"
            elif function == self.DMConfig.DMECMcommunication_functions[3]:
                              
                response= myECMComm.get_supplicant_by_id(kwargs["_supplicant_id_"]  )  
            #function "complete supplicant"
            elif function == self.DMConfig.DMECMcommunication_functions[4]:
                          
                response= myECMComm.set_supplicant_status_to_completed(kwargs["_supplicant_id_"]  )  
            #function "drop connection"
            elif function == self.DMConfig.DMECMcommunication_functions[5]:              
                response= myECMComm.drop_connection(kwargs["_client_id_"] )  
            else:
                loggerDMCOMM.error ("COMMUNICATION DM: communication function not found")

        elif protocol=="REST":
            #function "open supplicant"
            if function == self.DMConfig.DMECMcommunication_functions[0]:

                post_data = {
                    "supplicants": [
                        {

                            "task_times_to_ask": kwargs["_ask_times_"] ,
                            "task_hold_time": kwargs["_hold_time_"],
                            "RE2EL": kwargs["_RE2EL_"] ,
                            "supplicant_id": kwargs["_supplicant_id_"],
                            "task_id": kwargs["_task_id_"],
                            "OE2EL": kwargs["_OE2EL_"]
                        }
                    ]
                }

                headers = {'Content-type': 'application/json', 'Accept': '*/*'}
                try:
                    response_gotten = requests.post("http://127.0.0.1:5001/ecm/dm/supplicant-management/open", data=json.dumps(post_data),headers=headers)
                    response_json=response_gotten.json()
                    response=False
                except Exception as e:
                    loggerDMCOMM.error ("COMMUNICATION DM: Error reaching ECM or ENIM->" + str(e))
                    response=True

            else:
                loggerDMCOMM.error ("COMMUNICATION REST DecisionMakerECMCommunication: communication function not found: "+ str(function))

        elif protocol=="SocketTCP":

            if function == "TODO":
                pass
            else:
                loggerDMCOMM.error ("COMMUNICATION DM: communication function not found")

        elif protocol=="SocketUDP":
            if function == "TODO":
                pass
            else:
                loggerDMCOMM.error ("COMMUNICATION DM: communication function not found")  

        else:
            loggerDMCOMM.error ("COMMUNICATION DM: communication protocol not found")

        return response





class DecisionMakerSchedulerInterfaceCommunication():

    DMConfig=DecisionMakerConfig()
    EDConfig=EmbeddedDeviceConfig()

    def __init__(self) -> None:

        pass



    def communicate (self, protocol, function, **kwargs):

        if protocol=="OOP":
            if function == "TODO":
                pass                          
            else:
                loggerDMCOMM.error ("COMMUNICATION DM: communication function not found")
            
        elif protocol=="REST":

            #function "suspend task"
            if function == self.DMConfig.DMSIcommunication_functions[0]:
                loggerDMCOMM.debug ("REST suspend " + str(kwargs["_task_id_"] ) + str(kwargs["_task_type_"] ))
                headers = {'Content-type': 'application/json', 'Accept': '*/*'}
                #case app type is enhanced, we need to suspend both, client and server to release resources
                if (kwargs["_task_type_"]=="enhanced"):
                    #it seems there is no issue if we attemp to suspend a task that is already suspended
                    #response_gotten = requests.delete("http://192.168.1.100:80/suspend-task/"+kwargs["_task_id_"]+"_server")
                    response_gotten = requests.delete(self.EDConfig.getSuspendTaskEndpoint(_task_id_=kwargs["_task_id_"], _task_part_="server"))
                
                #whether it is enhanced or native, in both cases we must suspend the client part        
                #response_gotten = requests.delete("http://192.168.1.100:80/suspend-task/"+kwargs["_task_id_"]+"_client")
                response_gotten = requests.delete(self.EDConfig.getSuspendTaskEndpoint(_task_id_=kwargs["_task_id_"], _task_part_="client"))
                
                print ("+++++++++++++++++",response_gotten)
                loggerDMCOMM.debug ("REST response " + str(response_gotten))
                #response_json=response_gotten.json()
                #response=response_json  
                                        
            #function "resume task"
            elif function == self.DMConfig.DMSIcommunication_functions[1]:
                loggerDMCOMM.debug ("REST resume " + str(kwargs["_task_id_"] ) + str(kwargs["_task_type_"] ))
                headers = {'Content-type': 'application/json', 'Accept': '*/*'}
                message={"task_id":kwargs["_task_id_"],"type":kwargs["_task_type_"]}
                #case app type is enhanced, we need to suspend both, client and server to release resources
                response_gotten = requests.post(self.EDConfig.getResumeTaskEndpoint(), data=json.dumps(message),headers=headers)
                
                print ("+++++++++++++++++",response_gotten)
                loggerDMCOMM.debug ("REST response " + str(response_gotten))
                #response_json=response_gotten.json()
                #response=response_json     


            else:
                loggerDMCOMM.error ("COMMUNICATION REST DecisionMakerSchedulerInterfaceCommunication: communication function not found: "+ str(function))

        elif protocol=="SocketTCP":
            if function =="TODO":
                pass
            else:
                loggerDMCOMM.error ("COMMUNICATION DM: communication function not found")

        elif protocol=="SocketUDP":
            if function == "TODO":
                pass
            else:
                loggerDMCOMM.error ("COMMUNICATION DM: communication function not found")  

        else:
            loggerDMCOMM.error ("COMMUNICATION DM: communication protocol not found")

        return 0




class DecisionMakerTaskInterfaceCommunication():

    DMConfig=DecisionMakerConfig()
    EDConfig=EmbeddedDeviceConfig()

    def __init__(self) -> None:

        pass



    def communicate (self, protocol, function, **kwargs):
        response="NULL"
        if protocol=="OOP":
            #myTIComm=TaskInterface()
            #function "migrate task"
            if function == self.DMConfig.DMTIcommunication_functions[0]:
                loggerDMCOMM.debug ("migrating " + str(kwargs["_task_id_"] ) + " to pes "+ str(kwargs["_pes_"]) + " with IP " + str (kwargs["_edge_ip_"]))
                #response= myTIComm.migrate_task(task_id,edge_ip)                      
            else:
                loggerDMCOMM.error ("COMMUNICATION DM: communication function not found")
            
        elif protocol=="REST":

            #function "migrate task"
            if function == self.DMConfig.DMTIcommunication_functions[0]:
                loggerDMCOMM.debug ("REST migrating " + str(kwargs["_task_id_"] ) + " to pes "+ str(kwargs["_pes_"]) + " with IP " + str (kwargs["_edge_ip_"]))
                headers = {'Content-type': 'application/json', 'Accept': '*/*'}

                complete_address=kwargs["_edge_ip_"]
                _port_=complete_address[complete_address.find(":")+1:]
                _ip_= complete_address[0:complete_address.find(":")]
                message={"task_id":kwargs["_task_id_"],"pes":_ip_,"port":_port_}
                
                #response_gotten = requests.post("http://192.168.18.102:80/pes-update/", data=json.dumps(message),headers=headers)
                response_gotten = requests.post(self.EDConfig.getPesUpdateEndpoint(), data=json.dumps(message),headers=headers)
                print ("+++++++++++++++++",response_gotten)
                #response_json=response_gotten.json()
                #response=response_json

            # #function "suspend task"
            # elif function == self.DMConfig.DMTIcommunication_functions[1]:
            #     loggerDMCOMM.debug ("REST suspend " + str(kwargs["_task_id_"] ) + str(kwargs["_task_type_"] ))
            #     headers = {'Content-type': 'application/json', 'Accept': '*/*'}
            #     #case app type is enhanced, we need to suspend both, client and server to release resources
            #     if (kwargs["_task_type_"]=="enhanced"):
            #         #it seems there is no issue if we attemp to suspend a task that is already suspended
            #         #response_gotten = requests.delete("http://192.168.1.100:80/suspend-task/"+kwargs["_task_id_"]+"_server")
            #         response_gotten = requests.delete(self.EDConfig.getSuspendTaskEndpoint(_task_id_=kwargs["_task_id_"], _task_part_="server"))
                
            #     #whether it is enhanced or native, in both cases we must suspend the client part        
            #     #response_gotten = requests.delete("http://192.168.1.100:80/suspend-task/"+kwargs["_task_id_"]+"_client")
            #     response_gotten = requests.delete(self.EDConfig.getSuspendTaskEndpoint(_task_id_=kwargs["_task_id_"], _task_part_="client"))
                
            #     print ("+++++++++++++++++",response_gotten)
            #     #response_json=response_gotten.json()
            #     #response=response_json  
                                        
            # #function "resume task"
            # elif function == self.DMConfig.DMTIcommunication_functions[2]:
            #     loggerDMCOMM.debug ("REST resume " + str(kwargs["_task_id_"] ) + str(kwargs["_task_type_"] ))
            #     headers = {'Content-type': 'application/json', 'Accept': '*/*'}
            #     message={"task_id":kwargs["_task_id_"],"type":kwargs["_task_type_"]}
            #     #case app type is enhanced, we need to suspend both, client and server to release resources
            #     response_gotten = requests.post(self.EDConfig.getResumeTaskEndpoint(), data=json.dumps(message),headers=headers)
                
            #     print ("+++++++++++++++++",response_gotten)
            #     #response_json=response_gotten.json()
            #     #response=response_json     


            else:
                loggerDMCOMM.error ("COMMUNICATION REST DecisionMakerTaskInterfaceCommunication: communication function not found: "+ str(function))

        elif protocol=="SocketTCP":

            if function == "TODO":
                pass
            else:
                loggerDMCOMM.error ("COMMUNICATION DM: communication function not found")

        elif protocol=="SocketUDP":

            if function == "TODO":
                pass
            else:
                loggerDMCOMM.error ("COMMUNICATION DM: communication function not found")  

        else:
            loggerDMCOMM.error ("COMMUNICATION DM: communication protocol not found")

        return response





#Name:communicate
#applies polymorphism so whenever we want to communicate with any component, we send the 
#communication object, the protocol and the function as generic paramentes
#Parameters: object [object], protocol [str], function[str]
 #return: specific communicate method based on object type

def communicate (object, protocol, function, **kwargs):

    return object.communicate(protocol, function, **kwargs)





if __name__ == '__main__':
    
    myDMTMComm=DecisionMakerTaskMonitorCommunication()
    print (communicate(myDMTMComm, protocol="REST", function="glskd",  _task_id_="t1"))
    loggerDMCOMM.error ("COMMUNICATION DM: testing logging")

