#SchedulerInterface.py

#:::DESCRIPTION:::
#Implements the behaviour of SchedulerInterface Component. It 'reads' the initial EES configuration parameters (task_id, app_type, MAE2EL)
# and RTOS parameters (task_id, task_priority, OE2EL, idle_time).

#SchedulerInterface defines the following classes:

#   SchedulerInterfaceEngine: SchedulerInterfaceEngine represents the core of the SchedulerInterface component and its main function 
#     is to iterate through the scheduler parameters, format them and send them to the respective comnponents.
#   TaskMonitorAPI: provides all communication methods to communicate with TaskMonitor
#   SchedulerInterfaceAPI: provides all communication methods to communicate with SchedulerInterface




import json
import os
import time
import random
import SICommunication


class SchedulerInteractorAPI:
    
    # constructor
    def __init__(self, task_ids=[],task_priorities=[], task_OE2EL=[],  idle_time=0):
        
        self.task_ids = task_ids
        self.task_priorities = task_priorities
        self.task_OE2EL = task_OE2EL
        self.idle_time = idle_time
        
    #Name:get_update_from_rtos
    #Reads and sets the scheduler config parameters form a json file. It resets the variables for each iterarion.
    #Parameters: file_name
    #sets: 
    # * task_priorities [int]: Array with tasks' priorities  we will migrate (or not)
    # * task_OE2EL [int]: Array with tasks' observed end to end latency 
    # * idle_time [int]
    def get_update_from_rtos(self, file_name):
        
        path='EES_RTOSConfig'
        res_rtos=os.path.join(path,file_name)
        
        # Reset arrays
        self.task_ids = []
        self.task_priorities = []
        self.task_OE2EL = []
        
        # Opening JSON file
        f = open(res_rtos)
        # returns JSON object as a dictionary
        rtos_data = json.load(f)
        for i in rtos_data['tasks']:
            self.task_ids.append(i['task_id'])
            self.task_priorities.append(i['task_priority'])
            self.task_OE2EL.append(i['OE2EL'])
        self.idle_time = rtos_data['idle_time']

    # getter methods
    # The following methods get the scheduler parameters (by task id)
    def get_tasks_ids(self):
        return self.task_ids
        
    def get_task_priority(self, task_id):

        return self.task_priorities[self.task_ids.index(task_id)]
        
    def get_OE2EL(self, task_id):
        return self.task_OE2EL[self.task_ids.index(task_id)]
                
    def get_IDLE_time(self):
        return self.idle_time


    #Name:get_parameters
    #Formats the scheduler parameters into a dictionary.
    #Parameters: None
    #Returns: formatted scheduler parameters
    def get_parameters(self):
		
        # Sets data in the format:
        # e.g. parameters = {'tasks': {'t1': {'id': 't1', 'priority': 3, 'OE2EL': 50}}}
        tasks = dict.fromkeys(self.task_ids, [])
        for task_id, params in tasks.items():
            i = self.task_ids.index(task_id)
            tasks[task_id] = {'id':task_id,  'priority': self.task_priorities[i], 'OE2EL': self.task_OE2EL[i]}
        #parameters['idle_time'] = self.idle_time
        parameters = {'tasks':tasks}
        return parameters

class TaskMonitorAPI:
    def __init__(self):
        self.SIComm = SICommunication.SchedulerInterfaceTaskMonitorCommunication() #creates a common object for the class to be
    #used to implement communicaation with other components

    #Name:set_latest_available_data
    #sends the dictionary of scheduler parameters
    #Parameters: formatted scheduler parameters
    def set_latest_available_data(self, parameters):
        #SICommunication.communicate(self.SIComm,protocol="OOP", function="set parameters", _parameters_=parameters)
        SICommunication.communicate(self.SIComm, protocol="REST", function="set parameters", _parameters_=parameters)

    

class SchedulerInterfaceEngine:

    #constructor
    def __init__(self):
        self.SchedInteractor = SchedulerInteractorAPI()
        self.taskMonitor = TaskMonitorAPI()

    #Name:set_latest_available_data
    #sets the dictionary of scheduler parameters to TaskMonito component
    #Parameters: scheduler parameters
    def set_latest_available_data(self, parameters):
        self.taskMonitor.set_latest_available_data(parameters)


def simulate_scenario(rtos_file):
    obj1 = SchedulerInterfaceEngine()
    obj1.SchedInteractor.get_update_from_rtos(rtos_file) # get parameters from current rtos config file
    parameters = obj1.SchedInteractor.get_parameters()
    obj1.set_latest_available_data(parameters)
    time.sleep(10) # buffer



if __name__ == '__main__':

    obj1 = SchedulerInterfaceEngine()

    # Random iteration of RTOS config files every 5 seconds
    while True:
        print("Reading RTOS Config files...\n")
        files = os.listdir("EES_RTOSConfig")
        for file in random.sample(files,len(files)):
            if file.startswith("RTOS"):
                obj1.SchedInteractor.get_update_from_rtos(file) # get parameters from current rtos config file
                parameters = obj1.SchedInteractor.get_parameters()
                obj1.set_latest_available_data(parameters)
                time.sleep(10) # buffer
        print("Done\n")
        time.sleep(5)