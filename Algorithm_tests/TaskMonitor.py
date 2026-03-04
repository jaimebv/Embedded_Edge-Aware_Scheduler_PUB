from SystemConfigurations import TaskMonitorConfig
from queue import Queue
import json
import os
import time
import threading
from flask import Flask, jsonify, request
import TMCommunication
from PesDBManager import PESDBManager
import logging

dirname, filename = os.path.split(os.path.abspath(__file__))
log_path=str(dirname)
filename_log= log_path+"/LOGS/TM.log"

# create logger
loggerTM = logging.getLogger('TASK-MONITOR')
loggerTM.setLevel(logging.DEBUG)
# create console handler and set level to debug
chTM = logging.FileHandler(filename_log, mode='w')
chTM.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to chTM
chTM.setFormatter(formatter)
# add chTM to logger
loggerTM.addHandler(chTM)


class DesicionMakerAPI:



    def __init__(self):
        self.TMComm = TMCommunication.TaskMonitorDesicionMakerCommunication() #creates a common object for the class to be



    #Name:set_latest_issues
    #sends the dictionary of tasks issues
    #Parameters: formatted task parameters

    def set_latest_issues(self, parameters):
        #TMCommunication.communicate(self.TMComm, protocol="OOP", function="set issues", _parameters_=parameters)
        TMCommunication.communicate(self.TMComm, protocol="REST", function="set issues", _parameters_=parameters)





class TaskMonitorEngine ():
        
    E2EL_difference_threshold=1 #max accepted variation from MAE2EL in percentage
    _QR_VALUE=1
    MAX_QR_VALUE=5
    MIN_QR_VALUE=0
    issue_flag=[] #list that contains all detected issues
    _instance = None



    #Name:getInstance
    #returns the singleton object
    #Parameters: None
    #return: _instance[object]

    def getInstance():
        if TaskMonitorEngine._instance == None:
            TaskMonitorEngine()
        return TaskMonitorEngine._instance



    #constructor
    #Applies singleton, so we can only create one object of TaskMonitorEngine class
    #The object of TaskMonitorEngine class in turn creates objects of all other classes of the component
    #to be able to interact with them. All incomming or outgoing information goes through TaskMonitorEngine

    def __init__(self, zero_flag = True, ees_data = {}, default_param= {'tasks': {'t1': {'id': 't1', 'task_type': 'enhanced', 'priority': 3, 'OE2EL': 200, 'MAE2EL': 250}}}):

        if TaskMonitorEngine._instance != None:
            raise Exception("Singleton: there can only be one object")
        else:
            TaskMonitorEngine._instance = self
            self.TME_queue_SI= Queue(maxsize = 50)
            self.TME_queue_TI= Queue(maxsize = 50)
            self.myDesicionMakerAPI=DesicionMakerAPI()
            self.QR_task_values={} 
            dirname, filename = os.path.split(os.path.abspath(__file__))
            self.mypesdbmanager=PESDBManager(str(dirname)+ "\\pes_registry.db")
            self._key_lock = threading.Lock()
            TMConfig=TaskMonitorConfig()
            self.issue_flag_states=TMConfig.issue_flag_states #static variable-- possible states cannot change in runtime
            dirname, filename = os.path.split(os.path.abspath(__file__))
            res_ees=str(dirname)+ "\\EES_RTOSConfig\\EESConfig.json"  
            if(zero_flag):
                # Opening JSON file
                f = open(res_ees)
                # returns JSON object as a dictionary
                self.ees_data = json.load(f)["tasks"]
                f = open(res_ees)
                self.ees_resources_data = json.load(f)["totalResources"]
                zero_flag = False



    #Name:set_issues_data
    #sets issues data in DM REST Server.
    #Parameters: issues_data[dict]
    #return: request_response: 

    def set_issues_data(self,issues_data ):
        try:
            #set issues in DM REST Server
            request_response=self.myDesicionMakerAPI.set_latest_issues(issues_data)
                
        except Exception as e:
            request_response="NULL"

        return request_response



    #Name:increaseQR
    #increases Quality Rate by _QR_VALUE.
    #Parameters: QR[int]
    #return: QR[int] 

    def increaseQR(self, QR):
        if (QR>=self.MAX_QR_VALUE):
            QR=self.MAX_QR_VALUE
        else:
            QR=QR+self._QR_VALUE
        
        return QR



    #Name:decreaseQR
    #decreases Quality Rate by _QR_VALUE.
    #Parameters: QR[int]
    #return: QR[int] 

    def decreaseQR(self, QR):
        if (QR<=self.MIN_QR_VALUE):
            QR=self.MIN_QR_VALUE
        else:
            QR=QR-self._QR_VALUE
        
        return QR



    #Name:resetsQR
    #restores Quality Rate by the value defined in MAX_QR_VALUE.
    #Parameters: task_id[string]
    #return: QR[int] 

    def resetQR(self, task_id):
        self.QR_task_values[task_id]=self.MAX_QR_VALUE
        loggerTM.debug("QUALITY RATE SCORE: Resseting QR ")
    
         

    #Name:InvalidQR
    #Validates if Quality Rate has reached MIN_QR_VALUE .
    #Parameters: QR[int]
    #return: QR[int]

    def InvalidQR(self, QR):
        QR_flag=True

        if QR<=self.MIN_QR_VALUE:
            QR_flag=True
        else:
            QR_flag=False

        return QR_flag   



    #Name:TM_listener
    #implements listener_issues...
    #Parameters: None
    #return: None

    def TM_listener(self):
        first_iteration_flag=True  

        # A thread that always runs and acts when a message is put in the TME queue    
        # from  the endpoint /tm/si/latest_data
        while True:
            
            data=self.TME_queue_SI.get()
            device_information ={} #initializes a dictionary to store all device information to be sent to DM
            detected_issues =[] #initializes a dictionary to store all setected issues
            detected_issues.clear() #clears the list each iteration
            used_resources=0 #inits the amount of used resources
            
            #Iterates through all the tasks (information sent by SchedulerInterface component)
            for task_id in data:
                task_suspended_flag=False
                # case it is the first time running, all QR (Quality rate) values must be set to the max
                if(first_iteration_flag):
                    self.QR_task_values[task_id]=self.MAX_QR_VALUE

                self._key_lock.acquire() #locks the resources
                
                data[task_id]['app_type'] = self.ees_data[task_id]['app_type']
                data[task_id]['MAE2EL'] = self.ees_data[task_id]['MAE2EL']
                data[task_id]['resources_client'] = self.ees_data[task_id]['resources_client']
                data[task_id]['resources_server'] = self.ees_data[task_id]['resources_server']
                data[task_id]['QR']=self.QR_task_values[task_id]               
                
                self._key_lock.release()

                # Get latest known pes for all tasks in the system
                pes=self.mypesdbmanager.select_pes_by_task_id(task_id) # retireves current primary execution site of the task fro DB

                if pes:

                    loggerTM.debug("PES DB: Pes found in DB: "+ str(pes[0][1]) + " for task "+str(task_id))
                    data[task_id]['pes'] = pes[0][1]

                else:

                    if (data[task_id]['app_type'] == 'native'):
                        data[task_id]['pes']='pes_edge'
                    else:
                        data[task_id]['pes']='pes_local'

                    loggerTM.debug("PES DB: Assign default pes for task : "+ str(task_id) + " pes "+str(data[task_id]['pes']))

                # determine used resources by tasks in the system
                if (data[task_id]['state'] != "SUSPENDED"):
                    used_resources=used_resources +data[task_id]['resources_client']
                    
                    if (data[task_id]['pes'] == "pes_local"):
                        used_resources=used_resources +data[task_id]['resources_server']
                     

                #issue: timeout -> if task is in timeout state
                if (data[task_id]['state'] == "TIMEOUT"):
                    myQR=self.MIN_QR_VALUE
                    data[task_id]['issue'] = self.issue_flag_states[1]
                    detected_issues.append(self.issue_flag_states[1])

                #issue: task suspended -> if task is in suspended state
                elif (data[task_id]['state'] == "SUSPENDED"):
                    myQR=self.MIN_QR_VALUE
                    data[task_id]['issue'] = self.issue_flag_states[3]
                    detected_issues.append(self.issue_flag_states[3])

                #issue: not meeting deadline -> if (OE2EL-MAE2EL) > MAE2EL*E2EL_difference_threshold/100
                elif (data[task_id]['OE2EL'] > data[task_id]['MAE2EL']):
                    #TODO Quality Rate Score QR can implement policies to determine aspects such as
                    #   * number to decrease each time an issue is pressented
                    #   * number to increment each time OE2EL < MAE2EL
                    #   * max QR threshold (e.g. a task with higher priority has lower threshold to ensure QR reaches 0 faster)                   
                    myQR=self.decreaseQR(self.QR_task_values[task_id])
                    #case QR has not reached the min value yet (the task only experienced a high E2EL peak)
                    data[task_id]['issue'] = "None"
                    #validate if QR has reached the min value 
                    if (self.InvalidQR(myQR)):
                        #it is not only a peak, thus we must act 
                        data[task_id]['issue'] = self.issue_flag_states[0]
                        detected_issues.append(self.issue_flag_states[0])

                
                #issue: no detected issue        
                else:
                    myQR=self.increaseQR(self.QR_task_values[task_id])
                    data[task_id]['issue'] = "None"


                self.QR_task_values[task_id]=myQR # Assign QR value to the task


            first_iteration_flag=False
            
            loggerTM.info("RESOURCE MANAGEMENT: Resources used : "+ str(used_resources))
            if(self.checkResources(used_resources, self.ees_resources_data)):
                detected_issues.append(self.issue_flag_states[2])
            
           
            loggerTM.debug("DEVICE INFORMATION: detected_issues "+ str(detected_issues))    
            detected_issues = list( dict.fromkeys(detected_issues) )
            loggerTM.debug("DEVICE INFORMATION: detected_issues unique"+ str(detected_issues))   
            # set the dictionary with required data
            device_information['task_info'] = data
            device_information['resources']={"available": self.ees_resources_data, "used": used_resources}
            device_information['system_issues']=detected_issues
            
            loggerTM.info("DEVICE INFORMATION: "+ str(device_information))
            self.set_issues_data(device_information) 



    #Name:TI_listener
    #implements the method that listens to any incoming request from Task interface component
    #Parameters: None
    #return: None

    def TI_listener(self):
        while True:
            
            data=self.TME_queue_TI.get()
            
            self._key_lock.acquire() #locks the resources
            loggerTM.info("PES MANAGEMENT: Processing new pes: " + str(data))
            self.mypesdbmanager.insert_pes_into_registry(data["id"],data["new_pes"] )
            self.resetQR(data["id"])
            self._key_lock.release()



    #Name:checkResources
    #checks if there is any trouble with system resources
    #Parameters: used [int], total [int]
    #return: None

    def checkResources (self, used, total):
        check_res_issue=False

        if (used<total):
            check_res_issue=True
        elif (used==total):
            check_res_issue=False
        elif (used>total):
            check_res_issue=True
        else:
            check_res_issue=False
        return check_res_issue

        



#Defines the REST Server of the TM component

app=Flask(__name__)

data_new= {} 

@app.route('/')
def home():
    return "hello from TM Server"


@app.route('/tm/si/latest_data')
def get_latest_data():
    return jsonify(data_new)


@app.route('/tm/si/latest_data', methods=['POST'])
def set_latest_data():

    obj = TaskMonitorEngine.getInstance()
    data_new = request.get_json()
    obj.TME_queue_SI.put(data_new["tasks"])
    loggerTM.info("SI COMPONENT: Data notified: " + str(data_new["tasks"]))

    return jsonify(data_new)


@app.route('/tm/ti/pes_update', methods=['POST'])
def set_new_pes():

    obj = TaskMonitorEngine.getInstance()
    data_new = request.get_json()
    obj.TME_queue_TI.put(data_new)
    loggerTM.info("TI COMPONENT: Data notified: " + str(data_new))

    return jsonify(data_new)





if __name__ == '__main__':

    obj1=TaskMonitorEngine()

    #this thread will be constantly listening any incoming response from SI
    # NOTE: It modifies the value of supplicant_registry (TODO: mutex)
    t1 = threading.Thread(target=obj1.TM_listener, args=())
    t1.daemon= True
    t1.start()
    
    #this thread runs the REST server of TM Component
    t2= threading.Thread(target=lambda: app.run(host="0.0.0.0", port=4999, debug=False, use_reloader=False))
    t2.daemon= True
    t2.start()

    t3 = threading.Thread(target=obj1.TI_listener, args=())
    t3.daemon= True
    t3.start()
    

    while True:
        time.sleep(0.01)
