#ECM.py

#:::DESCRIPTION:::
#Implements the behaviour of Edge Communication Manager Component, which represents the only component
# allowed to communicate with ENIM. It forwards the messages from the embedded edge-aware agent to ENIM
# and viceversa.

#ECM defines the following classes:

#   ECMEngine: Represents the core of the ECM component and implements main functionalities
#   ENIMAPI: provides all communication methods to communicate with ENIM
#   ECMDBAPI:provides all communication methods to communicate with the database created for supplicants
#   ECM-REST-Server: the system implements a REST server on port 5001 as a separated thread, the REST server implements routes
#   in order to receive information from other components.

import logging
from SystemConfigurations import ECMConfig 
from SupplicantDBManager import SupplicantDBManager
from flask import Flask, jsonify, request
import threading
import time
import os
import requests
import json


dirname, filename = os.path.split(os.path.abspath(__file__))
log_path=str(dirname)
filename_log= log_path+"/LOGS/ECM.log"

# create logger
loggerECM = logging.getLogger('ECM')
loggerECM.setLevel(logging.DEBUG)
# create console handler and set level to debug
chECM = logging.FileHandler(filename_log, mode='w')
chECM.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to chECM
chECM.setFormatter(formatter)
# add chECM to logger
loggerECM.addHandler(chECM)


app=Flask(__name__)
logFlask = logging.getLogger('werkzeug')
logFlask.disabled = True

class ECMEngine ():

    _instance = None
    myECMConfig=ECMConfig()



    #Name:getInstance
    #returns the singleton object
    #Parameters: None
    #return: _instance[object]

    def getInstance():

        if ECMEngine._instance == None:
            ECMEngine()

        return ECMEngine._instance


    def __init__(self):

        if ECMEngine._instance != None:
            raise Exception("Singleton: there can only be one object")
        else:           
            dirname, filename = os.path.split(os.path.abspath(__file__))
            self._db_path=str(dirname)+ "\\supplicant_registry.db"
            self.myECMDBAPI=ECMDBAPI(self._db_path)
            self.myENIMAPI=ENIMAPI()
            self._my_threads=[]
    #TODO: a lock should be acquired every time we want to read or modify data from DB. However, this is to be done in ECM component



    #Name:open_supplicant
    #Defines a supplicant to ask ENIM for a node
    #Parameters: task_times_to_ask[int], task_hold_time[int], RE2EL[int], supplicant_id[str], task_id[str], OE2EL[int]
    #return: error_oppening [boolean]

    def open_supplicant(self, task_times_to_ask, task_hold_time, RE2EL, supplicant_id, task_id, OE2EL):

        try:
            loggerECM.info ("SUPPLICANT MANAGEMENT: open supplicant for task " +str(task_id)+ "-> task_times_to_ask "+ 
            str(task_times_to_ask)+ " task_hold_time "+ str(task_hold_time) + " and RE2EL: " + str(RE2EL))
            #TODO: open a new supplicant thread to ask ENIM for a node
            enim="192.199.99.1" #only setting a number for ENIM          
            supplicant_id= self.add_supplicant_to_registry(task_id, task_times_to_ask, task_hold_time, RE2EL,enim)
            t_supplicant= threading.Thread(target=self.threaded_supplicant, args=(supplicant_id, enim, task_times_to_ask,task_hold_time, task_id, RE2EL, OE2EL))
            t_supplicant.daemon= True
            t_supplicant.start()
            #self._my_threads.append[{task_id:t_supplicant}]          
            error_oppening=False #There was no problem opening the supplicant
        except Exception  as err:
            error_oppening=True #There was a problem, so the supplicant was not open
            supplicant_id=0
            loggerECM.error("SUPPLICANT MANAGEMENT: problem openning supplicant: " + str(err))

        return error_oppening, supplicant_id



    #Name:threaded_supplicant
    #Opens a supplicant thread to ask ENIM for a node, once this is done, it adds the supplicant to the supplicantsregistry
    #Parameters: task_times_to_ask[int], task_hold_time[int], RE2EL[int], supplicant_id[str], task_id[str]
    #return: error_oppening [boolean]

    def threaded_supplicant(self, supplicant_id, enim, task_times_to_ask, task_hold_time, task_id, RE2EL, OE2EL=0):
        
        times_asked=0
        client_id="client1_"+str(task_id)
        EE2EL=0
        node_IP="None"   

        self.drop_connection(client_id)
        #attempt to register a client with ENIM 3 times
        global client_location

        for connection_attempt in range (0,3):   
            
            
            register_response = self.myENIMAPI.register_client(client_id=client_id,RE2EL=RE2EL,location=client_location)    

            if register_response.status_code==200:
                break

            time.sleep(0.05)

        #case registering was correct
        if register_response.status_code==200:
            #print ("task_times_to_ask", task_times_to_ask, type(task_times_to_ask))
            #print ("times_asked", times_asked, type(times_asked))
            while int(task_times_to_ask)> times_asked:
                times_asked+=1
                loggerECM.debug ("SUPPLICANT MANAGEMENT: asking ENIM "+ str(enim) + " from supplicant "+
                str(supplicant_id)+ "->Times asked: "+ str(times_asked)  )                            
                suggested_node=self.myENIMAPI.perform_match(client_id)

                if suggested_node == "None":    
                    loggerECM.info ("MATCH MAKING: no match found by ENIM")
                else:
                    loggerECM.info ("MATCH MAKING: suggested_node is: "+ str(suggested_node))
                    EE2EL=int(suggested_node["endToEndLatency(ms)"])
                    node_IP=suggested_node["ipAddress"]
                    break                    

                time.sleep(int(task_hold_time))
        else:
            loggerECM.warning ("MATCH MAKING: it was not possible to register with ENIM")    

        data={"client_id":client_id, "supplicants":[
                {
                    "id":str(supplicant_id),
                    "task_id":str(task_id),
                    "status":"FINISHED",
                    "RE2EL":RE2EL,
                    "EE2EL":EE2EL,
                    "OE2EL":OE2EL,
                    "IP":str(node_IP)
                }
                ]
            }
        headers = {'Content-type': 'application/json', 'Accept': '*/*'}
        response_gotten = requests.post("http://127.0.0.1:5000/dm/ecm/supplicant_update", data=json.dumps(data),headers=headers)
        loggerECM.debug ("SUPPLICANT MANAGEMENT: closing supplicant " + str(supplicant_id))
        self.set_supplicant_status_to_finished(supplicant_id)



    #Name:cancel_supplicant
    #cancels a supplicant thread, once this is done, it sets the supplicant's status to CANCELED in the supplicantsregistry
    #this method can ONLY be invoked by DM Component
    #Parameters: supplicant_id[str]
    #return: error_cancelling [boolean]

    def cancel_supplicant(self, supplicant_id):

        #TODO:interrupt/close the supplicant thread
        error_cancelling=self.myECMDBAPI.db_cancel_supplicant(supplicant_id)

        return error_cancelling



    #Name:set_supplicant_status_to_completed
    #Sets the supplicant status to completed
    #Parameters: supplicant_id[str]
    #return: error_setting [boolean]

    def set_supplicant_status_to_completed(self, supplicant_id):

        error_setting=self.myECMDBAPI.db_set_supplicant_status_to_completed(supplicant_id)

        return error_setting



    #Name:set_supplicant_status_to_finished
    #Sets the supplicant status to finished
    #Parameters: supplicant_id[str]
    #return: error_setting [boolean]

    def set_supplicant_status_to_finished(self, supplicant_id):

        error_setting=self.myECMDBAPI.db_set_supplicant_status_to_finished(supplicant_id)

        return error_setting



    #Name:get_supplicant
    #get all supplicants that satisfy the condition established by the policy from supplicantregistry (DB) 
    #Parameters: task_id[str],policy_name[str]
    #policy_name can be:
    #* one_per_task: the system allows to have only one supplicant open per task at the time (in parallel)
    #  but there could be several supplicants at the same time attending different tasks
    #* one_at_the_time: the system allows to have ONLY one supplicant running at the time (independently of the task it aims to attend)
    #return: supplicant_data [list of tuples]

    def get_supplicant(self, task_id,policy_name):
        
        supplicant_data=self.myECMDBAPI.db_get_supplicant(task_id,policy_name)
        
        return supplicant_data



    #Name:get_supplicant_by_id
    #Retrieves supplicant information
    #Parameters: supplicant_id[str]
    #return: supplicant_data [list]

    def get_supplicant_by_id(self, supplicant_id):
        
        supplicant_data=self.myECMDBAPI.db_get_supplicant_by_id(supplicant_id)
        
        return supplicant_data



    #Name:add_supplicant_to_registry
    #Adds a new supplicant to the local supplicant registry
    #Parameters: supplicant_id[str],task_id[str], task_times_to_ask[int], task_hold_time[int], RE2EL[int]
    #return:None

    def add_supplicant_to_registry(self,task_id, task_times_to_ask, task_hold_time, RE2EL,enim):
        
        supplicant_id=self.myECMDBAPI.db_add_supplicant_to_registry(task_id, task_times_to_ask, task_hold_time, RE2EL,enim)
       
        return supplicant_id



    #Name:delete_supplicant_from_registry
    #Deletes a given supplicant from the local supplicant registry
    #Parameters: issue_id[str]
    #return: None

    def delete_supplicant_from_registry(self,issue_id):

        loggerECM.debug("SUPPLICANT MANAGEMENT: deleting supplicant from local registry")
        self.myECMDBAPI.db_delete_supplicant_from_registry(issue_id)



    #Name:drop_connection
    #Drops a suggested connection by ENIM
    #Parameters: client_id[str]
    #return: None

    def drop_connection (self, client_id):

        loggerECM.debug ("MATCH MAKING: drop match for client: " + str(client_id))
        self.myENIMAPI.drop_match(client_id)





class ENIMAPI():

    def __init__(self) -> None:

        pass



    #Name:register_client
    #Registers a certain client with ENIM
    #Parameters: client_id[str],RE2EL[int],location[int]
    #return: None

    def register_client(self,client_id, RE2EL,location):

        
        client_to_register = {
            "id": client_id,
            "reqNetwork": 1,
            "reqResource": 1,
            "location": location,
            "heartBeatInterval": 15000000000
        }
        
        loggerECM.info ("MATCH MAKING: registering client" + str(client_to_register))

        headers = {'Content-type': 'text/plain', 'Accept': '*/*'}
        register_response = requests.post("http://127.0.0.1:4567/rest/client/register", data=json.dumps(client_to_register),headers=headers)
        
        return register_response



    #Name:match_making
    #Asks ENIM for a match with a registered node
    #Parameters: client_id[str],RE2EL[int],location[int]
    #return: None

    def match_making(self,client_id):

        match_making_data={"id" : client_id}
        headers = {'Content-type': 'text/plain', 'Accept': '*/*'}
        match_response = requests.post("http://127.0.0.1:4567/rest/client/assign", data=json.dumps(match_making_data),headers=headers)
        
        return match_response



    #Name:perform_match
    #Asks ENIM for a match with a registered node
    #Parameters: client_id[str]
    #return: None

    def perform_match(self,client_id):

        suggested_node="None"            
        match_response=self.match_making(client_id)

        if "FAILED" in match_response.content.decode('ascii'):
            loggerECM.info ("MATCH MAKING: ENIM did not find a match ->"+ str(match_response.content.decode('ascii')))
        elif match_response.content.decode('ascii')=='200':
                loggerECM.info ("MATCH MAKING: got a match from ENIM")
                suggested_node=self.get_match(client_id)                
        elif "this" in match_response.content.decode('ascii'):
            loggerECM.debug ("MATCH MAKING: disconnecting again from previous match and requesting a new one")
            self.drop_match(client_id)
            time.sleep(0.2)
            self.match_making(client_id)
            suggested_node=self.get_match(client_id)
        else:
            loggerECM.error ("MATCH MAKING: unknown issue with ENIM")

        return suggested_node



    #Name:get_match
    #Retrieves match making information
    #Parameters: client_id[str]
    #return: None

    def get_match(self, client_id):

        node_response = requests.get("http://127.0.0.1:4567/rest/client/get_node/"+client_id)
        suggested_node=json.loads(node_response.content.decode("utf-8"))
       
        return suggested_node



    #Name:drop_match
    #Drops a suggested match given by ENIM
    #Parameters: client_id[str]
    #return: None

    def drop_match(self,client_id):

        disconnect_data={"id" : client_id, "message" : "job_done"}
        headers = {'Content-type': 'text/plain', 'Accept': '*/*'}
        disconnect_response = requests.post("http://127.0.0.1:4567/rest/client/disconnect", data=json.dumps(disconnect_data),headers=headers)

        if disconnect_response.content.decode("ascii")=='200':
            pass
        else:
            loggerECM.error ("MATCH MAKING: unsuccessful request-> dop match")



class ECMDBAPI():

    #contructor: creates an object to interact with DB
    def __init__(self,db_path):
        self.myDBManager=SupplicantDBManager(db_path)  



    #Name:db_cancel_supplicant
    #sets the supplicant's status to CANCELED in the supplicantsregistry
    #Parameters: supplicant_id[str]
    #return: error_cancelling [boolean]

    def db_cancel_supplicant(self, supplicant_id):
        try:
            loggerECM.debug ("SUPPLICANT MANAGEMENT: cancelling supplicant in db: " +str(supplicant_id))
            self.myDBManager.set_supplicant_status_to_canceled(supplicant_id)
            error_cancelling=False #There was no problem closing the supplicant
        except:
            error_cancelling=True #There was a problem, so the supplicant was not canceled
        
        return error_cancelling



    #Name:db_get_supplicant
    #get all supplicants that satisfy the condition established by the policy from supplicantregistry (DB) 
    #Parameters: task_id[str],policy_name[str]
    #policy_name can be:
    #* one_per_task: the system allows to have only once supplicant open per task at the time (in parallel)
    #  but there could be several supplicants at the same time attending different tasks
    #* one_at_the_time: the system allows to have ONLY one supplicant running at the time (independently of the task it aims to help)
    #return: supplicant_data [list of tuples]

    def db_get_supplicant(self,task_id,policy_name):

        if policy_name == 'one_at_the_time':
            supplicant_data=self.myDBManager.select_supplicants_by_status()        
        elif policy_name == 'one_per_task':
            supplicant_data=self.myDBManager.select_supplicants_by_task_id(task_id)        
        else:            
            #case we want to implement more policies, they should go here!
            supplicant_data=self.myDBManager.select_supplicants_by_status()
        
        return supplicant_data



    #Name:db_get_supplicant_by_id
    #Retrieves supplicant's information from db
    #Parameters: supplicant_id[str]
    #return: supplicant_data [list]

    def db_get_supplicant_by_id(self,supplicant_id):

        supplicant_data=self.myDBManager.select_supplicants_by_supplicant_id(supplicant_id)

        return supplicant_data



    #Name:db_set_supplicant_status_to_completed
    #Sets supplicant status to completed in db
    #Parameters: supplicant_id[str]
    #return: error setting [boolean]
        
    def db_set_supplicant_status_to_completed(self,supplicant_id):

        try:            
            self.myDBManager.set_supplicant_status_to_completed(supplicant_id)
            error_setting=False #There was no problem closing the supplicant
        except Exception as err:
            error_setting=True #There was a problem, so the supplicant was not canceled
            loggerECM.error ("SUPPLICANT MANAGEMENT: error while setting suplicant state-> "+ str(err))
        
        return error_setting



    #Name:db_set_supplicant_status_to_finished
    #Sets supplicant status to finished in db
    #Parameters: supplicant_id[str]
    #return: error setting [boolean]

    def db_set_supplicant_status_to_finished(self,supplicant_id):

        try:           
            self.myDBManager.set_supplicant_status_to_finished(supplicant_id)
            error_setting=False #There was no problem closing the supplicant
        except Exception as err:
            error_setting=True #There was a problem, so the supplicant was not canceled
            loggerECM.error ("SUPPLICANT MANAGEMENT: error while setting suplicant state-> "+ str(err))
        
        return error_setting



    #Name:db_add_supplicant_to_registry
    #adds a new supplicant to the local supplicant registry db
    #Parameters: task_id[str], task_times_to_ask[int], task_hold_time[int], RE2EL[int]
    #return:supplicant_id [str]

    def db_add_supplicant_to_registry(self,task_id, task_times_to_ask, task_hold_time, RE2EL, enim):
        
        #TODO: get ENIM IP
        loggerECM.debug("SUPPLICANT MANAGEMENT: adding supplicant to local registry")
        supplicant_id=self.myDBManager.insert_supplicant_into_registry(task_id, enim, task_hold_time, task_times_to_ask, RE2EL)
        
        return supplicant_id



    #Name:db_delete_supplicant_from_registry
    #Deletes a given supplicant from the local supplicant registry
    #Parameters: supplicant_id[str]
    #return: None

    def db_delete_supplicant_from_registry(self,supplicant_id):
        loggerECM.debug("SUPPLICANT MANAGEMENT: deleting supplicant from local registry")
        self.myDBManager.delete_supplicant(supplicant_id)





#REST Server of the ECM component

supplicant_data_new= {} 
supplicant_update={}
client_location=0

@app.route('/')
def home():

    return "hello from ECM Server"



@app.route('/ecm/dm/supplicant-management')
def get_latest_issue():

    #TODO: This should have a mutex as it could happen at the same time when someone is writing the variable
    return jsonify(supplicant_data_new)



@app.route('/ecm/dm/supplicant-management/open', methods=['POST'])
def open_supplicant_task():
    
    supplicant_data=request.get_json()  
    loggerECM.debug("SUPPLICANT MANAGEMENT: supplicant data in ECM: " + str(supplicant_data))

    for supplicant_position in range(0, len(supplicant_data['supplicants'])):
               
        task_times_to_ask=supplicant_data['supplicants'][supplicant_position]['task_times_to_ask']
        task_hold_time=supplicant_data['supplicants'][supplicant_position]['task_hold_time']
        RE2EL=supplicant_data['supplicants'][supplicant_position]['RE2EL']
        supplicant_id=supplicant_data['supplicants'][supplicant_position]['supplicant_id']
        task_id=supplicant_data['supplicants'][supplicant_position]['task_id']    
        OE2EL=supplicant_data['supplicants'][supplicant_position]['OE2EL'] 
        obj1.open_supplicant(task_times_to_ask, task_hold_time, RE2EL, supplicant_id, task_id,OE2EL)
        #TODO: This should have a mutex as it could happen at the same time when someone is reading the variable
        
    return jsonify(supplicant_data)
    



@app.route('/ecm/dm/supplicant-management/drop-connection/<client_id>')
def drop_connection_from_enim(client_id):
    
    response= {"Client_id":client_id, "Result": 200}
    obj1.drop_connection(client_id)  

    return jsonify(response),200


@app.route('/ecm/simulator/clientlocation')
def get_location():
    global client_location
    return jsonify(client_location)

@app.route('/ecm/simulator/clientlocation/<location>', methods=['POST'])
def set_location(location):
    global client_location
    client_location=int(location)
    return jsonify("OK"),200






if __name__ == '__main__':
    obj1=ECMEngine()
    #this thread runs the REST server of DM Component
    t3= threading.Thread(target=lambda: app.run(port=5001, debug=True, use_reloader=False))
    t3.daemon= True
    t3.start()

    while True:

        time.sleep(0.5)
else:
    obj1=ECMEngine()