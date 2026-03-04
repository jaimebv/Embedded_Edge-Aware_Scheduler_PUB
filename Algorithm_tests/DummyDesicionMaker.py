#DesicionMaker.py

#:::DESCRIPTION:::
#Implements the behaviour of DecisionMaker Component, which corresponds to the core of 
#the embedded edge-aware agent. It decides whether certain task switches pes or not based on policies.

#DesicionMaker defines the following classes:

#   DecisionMakerEngine: DecisionMakerEngine represents the core of the DM component and its main function 
#     is to put everything together. All incoming and sending information goes through the engine before.
#     This element shall run independently of the incoming data from any other external component. Therefore, 
#     it uses the latest available data to make a decision. 
#   TaskMonitorAPI: provides all communication methods to communicate with TaskMonitor
#   TaskInterfaceAPI:provides all communication methods to communicate with TaskInterface
#   SchedulerInterfaceAPI: provides all communication methods to communicate with SchedulerInterface
#   ECMAPI: provides all communication methods to communicate with ECM
#   DecisionHandler: implements the algorithms to make a decision based on the detected issues by TaskMonitor Component
#   DM-REST-Server: the system implements a REST server as a separated thread, in order to receive information from
#   any other component. 

import os
import logging
from SystemConfigurations import DecisionMakerConfig
import DMCommunication
import threading
import time
from queue import Queue
from flask import Flask, jsonify, request
from AttendedScore import AttendedScoreManager
from datetime import datetime
#from Supplicant_ID_Generator import Supplicant_Manager #UNCOMMENT in case we want to generate our own supplicant_id
#as for now, the sqlite table auto_increments the value of supplicant_id, thus, this option is disabled

dirname, filename = os.path.split(os.path.abspath(__file__))
log_path=str(dirname)
filename_log= log_path+"/LOGS/DM.log"

# create logger
loggerDM = logging.getLogger('DECISION-MAKER')
loggerDM.setLevel(logging.DEBUG)
# create console handler and set level to debug
chDM = logging.FileHandler(filename_log, mode='w')
chDM.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to chDM
chDM.setFormatter(formatter)
# add chDM to logger
loggerDM.addHandler(chDM)




now = datetime.now()
now=str(now.strftime("%d-%m-%Y-%H_%M_%S"))
now=now.replace(" ", "_")
now=now.replace(":", "_")
now=now.replace(".", "_")

dirname, filename = os.path.split(os.path.abspath(__file__))
log_path=str(dirname)
filename_data_log= log_path+"/LOGS/dataRaw_"+str(now)+".log"


print(filename_data_log)
# create logger
loggerDataLogger = logging.getLogger('DataLogger')
loggerDataLogger.setLevel(logging.DEBUG)
# create console handler and set level to debug
chDataLogger = logging.FileHandler(filename_data_log, mode='w')
chDataLogger.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('{"time":"%(asctime)s", "data":%(message)s}')
# add formatter to chDataLogger
chDataLogger.setFormatter(formatter)
# add chDataLogger to logger
loggerDataLogger.addHandler(chDataLogger)





TIME_ITERATION_DECISION_MAKER_MS=300


class DecisionHandler():

    DMConfig=DecisionMakerConfig()  #creates an object to define configurations from a common file 
    myDMTIComm=DMCommunication.DecisionMakerTaskInterfaceCommunication() #creates a common object for the class to be
    myDMSIComm=DMCommunication.DecisionMakerSchedulerInterfaceCommunication() #creates a common object for the class to be

    issues_data={} #initializes a dict to accumulate issues



    #constructor
    def __init__(self) -> None:

        self._TIME_OUT_THRESHOLD=3000



    #Name:issue_not_meeting_deadline
    #Implements the algorithm needed to make a decision when a task is not meeting its deadline.
    #Parameters: task_id[string], issues[dict]
    #return: 
    # * task_id [str]: the id of the task we will migrate (or not)
    # * pes_flag [str]: the new decided primary execution site for the task
    # * RE2EL [int]: in case we migrate to a new edge, we request ENIM an edge with <= latency than RE2EL  
    # * task_priority [int]: the priority of the task being attended
    # * OE2EL [int]: the Observed End-to-End Latency
    # * action [str]: the action to be taken
    
    def issue_not_meeting_deadline(self,task_id, issues):

        loggerDM.info("ISSUE MANAGEMENT: issue_not_meeting_deadline case has been selected")
        action="Migrate"
        task_priority=issues[task_id]["priority"]
        app_type=issues[task_id]["app_type"]
        app_part="client"

        if issues[task_id]["app_type"]=="native": #edge-native tasks can only run at the edge
            pes_flag="new_edge_pes_flag"
            RE2EL=int(issues[task_id]["MAE2EL"] *0.9)  #RE2EL= 90% of MAE2EL 
            OE2EL=int(issues[task_id]["OE2EL"])
            #TODO:RE2EL should be defined based on a policy. Now, we only ask a RE2EL= 90% of MAE2EL as a 
            #very basic policy 
        elif issues[task_id]["app_type"]=="enhanced": #by default we attempt to run edge-enhanced tasks at the edge
            pes_flag="new_edge_pes_flag"
            RE2EL=int(issues[task_id]["MAE2EL"] *0.9) #RE2EL= 90% of MAE2EL
            OE2EL=int(issues[task_id]["OE2EL"])
        #case task is local, we cannot migrate it and thus must migrate other tasks to edge in order to release local resources
        else:
            #iterate to find a task that is running locally and can be migrated
            for task_id_secondary in issues:
                #print ("//////////////", issues)
                #print ("//////////////", task_id_secondary)
                #case sec_task is enhanced and it was running locally and its priority is lower than current local task
                if issues[task_id_secondary]["app_type"]=="enhanced" and issues[task_id_secondary]["pes"]=="pes_local" and issues[task_id]["priority"]<issues[task_id_secondary]["priority"]:                   
                    #attempt switch secondary task to edge
                    #print ("//////////////ATTENDEND", issues[task_id_secondary]["attended"])
                    if issues[task_id_secondary]["attended"] > 0:
                        loggerDM.debug("ISSUE MANAGEMENT: We have already act on secondary task: "+ str(task_id_secondary))                       
                    else: 

                        loggerDM.debug("ISSUE MANAGEMENT: acting on a secondary task: "+ str(task_id_secondary))
                        #update action parameters
                        pes_flag="new_edge_pes_flag"
                        RE2EL=int(issues[task_id_secondary]["MAE2EL"] *0.9)  #RE2EL= 90% of MAE2EL
                        OE2EL=int(issues[task_id_secondary]["OE2EL"])
                        task_id=task_id_secondary
                        break

                else: 
                #case no sec_task was found. there is nothing else to do
                #NOTE: Here we assuume that local scheduler has already left all other tasks with lower priority in ready state
                #in order to assign all available resources to the local tasks with higher priority. That's why we say
                #there is nothing else to do.
                    pes_flag="hold_pes_flag"
                    action="Hold"
                    RE2EL=0
                    OE2EL=0         

        return task_id, pes_flag,RE2EL,task_priority, OE2EL,action,app_type,app_part



    #Name:issue_timeout
    #Implements the algorithm needed to make a decision when a task isin timeout state.
    #Parameters: task_id[string], issues[dict]
    #return: 
    # * task_id [str]: the id of the task we will migrate (or not)
    # * pes_flag [str]: the new decided primary execution site for the task
    # * RE2EL [int]: in case we migrate to a new edge, we request ENIM an edge with <= latency than RE2EL  
    # * task_priority [int]: the priority of the task being attended
    # * OE2EL [int]: the Observed End-to-End Latency
    # * action [str]: the action to be taken
    
    def issue_timeout(self,task_id, issues):

        loggerDM.info("ISSUE MANAGEMENT: issue_timeout case has been selected")
        action="Migrate" #initializes issue action
        task_priority=issues[task_id]["priority"] #initializes task priority
        app_type=issues[task_id]["app_type"]
        app_part="client"

        if issues[task_id]["app_type"]=="native": #edge-native tasks can only run at the edge
            pes_flag="new_edge_pes_flag"
            RE2EL=int(issues[task_id]["MAE2EL"] *0.9)  #RE2EL= 90% of MAE2EL 
            OE2EL=int(issues[task_id]["OE2EL"])
            #TODO:RE2EL should be defined based on a policy. Now, we only ask a RE2EL= 90% of MAE2EL as a 
            #very basic policy 
        elif issues[task_id]["app_type"]=="enhanced": #by default we attempt to run edge-enhanced tasks at the edge
            pes_flag="new_edge_pes_flag"
            RE2EL=int(issues[task_id]["MAE2EL"] *0.9) #RE2EL= 90% of MAE2EL
            OE2EL=int(issues[task_id]["OE2EL"])
        #case task is local, we cannot migrate it and thus must migrate any other task to edge in order to release local resources
        else:
            #iterate to find a task that is running locally and can be migrated
            for task_id_secondary in issues:

                #case sec_task is enhanced and it was running locally and its priority is lower than current local task
                if issues[task_id_secondary]["app_type"]=="enhanced" and issues[task_id_secondary]["pes"]=="pes_local" and issues[task_id]["priority"]<issues[task_id_secondary]["priority"]:                   
                    #attempt switch secondary task to edge
                    if issues[task_id_secondary]["attended"] > 0:
                        loggerDM.debug("ISSUE MANAGEMENT: We have already act on secondary task: "+ str(task_id_secondary))                       
                    else: 

                        loggerDM.debug("ISSUE MANAGEMENT: acting on a secondary task: "+ str(task_id_secondary))
                        #update action parameters
                        pes_flag="new_edge_pes_flag"
                        RE2EL=int(issues[task_id_secondary]["MAE2EL"] *0.9)  #RE2EL= 90% of MAE2EL
                        OE2EL=int(issues[task_id_secondary]["OE2EL"])
                        task_id=task_id_secondary
                        break

                else: 
                #case no sec_task was found. there is nothing else to do
                #NOTE: Here we assuume that local scheduler has already left all other tasks with lower priority in ready state
                #in order to assign all available resources to the local tasks with higher priority. That's why we say
                #there is nothing else to do.
                    pes_flag="hold_pes_flag"
                    action="Hold"
                    RE2EL=0
                    OE2EL=0         

        return task_id, pes_flag,RE2EL,task_priority, OE2EL,action, app_type, app_part



    #Name:issue_no_enough_resources
    #Implements the algorithm needed to make a decision when there are not enough resources to run all tasks in the device.
    #Parameters: task_id[string], issues[dict]
    #return: 
    # * task_id [str]: the id of the task we will attend
    # * pes_flag [str]: the new decided primary execution site for the task
    # * RE2EL [int]: in case we migrate to a new edge, we request ENIM an edge with <= latency than RE2EL  
    # * task_priority [int]: the priority of the task being attended
    # * OE2EL [int]: the Observed End-to-End Latency
    # * action [str]: the action to be taken
    
    def issue_no_enough_resources(self,task_id,issues):

        loggerDM.info ("ISSUE MANAGEMENT: issue_no_enough_resources case has been selected")
        action="Suspend"
        #print("ISSUES IN METHOD: ", issues)
        pes_flag="None"
        RE2EL =0
        OE2EL=0
        task_priority=1
        app_type="local"
        app_part="client"

        tasks_to_suspend_dict={} #initializes a dict that will contain all tasks that can be suspended

        for task_id in issues:
            
            #case issue_type !=None and the task has not been attended yet and it is not suspended already, put it into a dictionary
            if issues[task_id]["issue"] != "None" and issues[task_id]["attended"] <= 0 and issues[task_id]["state"] != "SUSPENDED":
                tasks_to_suspend_dict[task_id]=issues[task_id]["priority"] #accumulates only active tasks in a dictionary
        #print ("///////////tasks_to_suspend_dict", tasks_to_suspend_dict)
        if tasks_to_suspend_dict: 
            #get the task with the lowest priority, so we suspend it in order to release resources
            task_to_suspend= min(tasks_to_suspend_dict, key=tasks_to_suspend_dict.get) #gets the task with min priority  
            task_priority=tasks_to_suspend_dict[task_to_suspend]
            loggerDM.debug ("ISSUE MANAGEMENT: task to suspend-> "+str(task_to_suspend) + "type: " + str(issues[task_to_suspend]["app_type"]) + "with priority: " + str(task_priority))
            #send request to suspend the task
            #TODO: We could validate if the task has been properly suspended
            app_type=issues[task_to_suspend]["app_type"]
            #DMCommunication.communicate (self.myDMTIComm, protocol="REST", function="suspend task", _task_id_=task_to_suspend, _task_type_=issues[task_to_suspend]["app_type"])
            action="Suspend"
        else:
            loggerDM.debug ("ISSUE MANAGEMENT: there is no task to suspend in order to release resources")
            action="Hold"

        

        return  task_to_suspend, pes_flag,RE2EL, task_priority,OE2EL,action, app_type, app_part



    #Name:issue_task_suspended
    #Implements the algorithm needed to make a decision and attempt to resume a task when possible.
    #Parameters: task_id[string], issues[dict]
    #return: 
    # * task_id [str]: the id of the task we will attend
    # * pes_flag [str]: the new decided primary execution site for the task
    # * RE2EL [int]: in case we migrate to a new edge, we request ENIM an edge with <= latency than RE2EL  
    # * task_priority [int]: the priority of the task being attended
    # * OE2EL [int]: the Observed End-to-End Latency
    # * action [str]: the action to be taken
    
    def issue_task_suspended(self,task_id,issues):
        loggerDM.info ("ISSUE MANAGEMENT: issue_task_suspended case has been selected")
        action="None"
        task_to_act=task_id
        pes_flag="None"
        RE2EL =0
        OE2EL=0
        task_priority=1
        app_type=issues[task_id]["app_type"]
        app_part="client"

        suspended_task_dict={}
        active_task_dict={}
        for task_id_ in issues:
            #TODO: check if the suspended task has a higher priority than running tasks
            #case there is a suspended task that can be resumed (if there are available resources)
            if  (issues[task_id_]["state"] == "SUSPENDED" and issues[task_id_]["attended"] <= 0):
                #loggerDM.debug("RESOURCES MANAGEMENT:There is a suspended task: " + str(task_id_) )
                
                suspended_task_priority= issues[task_id_]["priority"]
                #loggerDM.debug("RESOURCES MANAGEMENT:Checking task priority: "+ str(suspended_task_priority))
                suspended_task_dict[task_id_]=suspended_task_priority
            else:    
                #loggerDM.debug("RESOURCES MANAGEMENT:There is an active task that could be suspended: " + str(task_id_))
                active_task_priority= issues[task_id_]["priority"]
                active_task_dict[task_id_]=active_task_priority
                #loggerDM.debug("RESOURCES MANAGEMENT:Checking task priority: "+ str(active_task_priority))

        #TODO compare highest suspended-task priority vs lowest active-task priority
        #case st-priority> at-priority, clear required resources to allow suspended task to run again
        task_to_suspend= min(active_task_dict, key=active_task_dict.get) #gets the task with min priority
        task_to_resume= max(suspended_task_dict, key=suspended_task_dict.get) #gets the task with min priority
        loggerDM.debug("RESOURCES MANAGEMENT:active_task_dict: " + str(active_task_dict))
        loggerDM.debug("RESOURCES MANAGEMENT:suspended_task_dict: " + str(suspended_task_dict))

        
        if (active_task_dict[task_to_suspend]<suspended_task_dict[task_to_resume] and issues[task_to_resume]["attended"]<=0):
            #we have  a high-priority task suspended
            task_priority=suspended_task_dict[task_to_resume] #assign the priority of the suspended task to the variable
            loggerDM.debug("RESOURCES MANAGEMENT:There is a high-priority task suspended: " + str(task_to_resume))
            loggerDM.debug("RESOURCES MANAGEMENT:We could suspend: " + str(task_to_suspend)+ "to release resources")
            if (issues[task_to_resume]["app_type"]=="local"):
                loggerDM.debug("RESOURCES MANAGEMENT:suspend task: " + str(task_to_suspend))
                pes_flag="hold_pes_flag"
                app_type=issues[task_to_suspend]["app_type"]
                # DMCommunication.communicate (self.myDMTIComm, protocol="REST", function="suspend task", _task_id_=task_to_suspend, _task_type_=issues[task_to_suspend]["app_type"])
                # loggerDM.debug("RESOURCES MANAGEMENT:resume task: " + str(task_to_resume))
                # DMCommunication.communicate (self.myDMTIComm, protocol="REST", function="resume task", _task_id_=task_to_resume, _task_type_="client")
                action="Suspend"
                task_to_act=task_to_resume

            elif issues[task_id]["app_type"]=="native": #edge-native tasks can only run at the edge
                pes_flag="new_edge_pes_flag"
                RE2EL=int(issues[task_id]["MAE2EL"] *0.9)  #RE2EL= 90% of MAE2EL 
                OE2EL=int(issues[task_id]["OE2EL"])
                #TODO:RE2EL should be defined based on a policy. Now, we only ask a RE2EL= 90% of MAE2EL as a 
                #very basic policy 
                action="Migrate"
                task_to_act=task_to_resume

            elif issues[task_id]["app_type"]=="enhanced": #by default we attempt to run edge-enhanced tasks at the edge
                pes_flag="new_edge_pes_flag"
                RE2EL=int(issues[task_id]["MAE2EL"] *0.9) #RE2EL= 90% of MAE2EL
                OE2EL=int(issues[task_id]["OE2EL"])
                action="Migrate"
                task_to_act=task_to_resume
            else:
                loggerDM.error("ISSUE MANGEMENT: app_type not regonized: "+ str(issues[task_id]["app_type"]))


        return  task_to_act, pes_flag,RE2EL, task_priority,OE2EL,action, app_type, app_part                        


    #Name:issue_resume_native
    #Implements the algorithm needed to resume a suspended edge-native task.
    #Parameters: task_id[string], issues[dict]
    #return: 
    # * task_id [str]: the id of the task we will attempt to resume
    # * pes_flag [str]: the new decided primary execution site for the task
    # * RE2EL [int]: in case we migrate to a new edge, we request ENIM an edge with <= latency than RE2EL  
    # * task_priority [int]: the priority of the task being attended
    # * OE2EL [int]: the Observed End-to-End Latency
    # * action [str]: the action to be taken
    
    def issue_resume_native(self,task_id,issues):


        loggerDM.info("ISSUE MANAGEMENT: issue_resume_native case has been selected")
        action="Migrate"
        task_priority=issues[task_id]["priority"]
        app_type=issues[task_id]["app_type"]
        app_part="client"


        pes_flag="new_edge_pes_flag"
        RE2EL=int(issues[task_id]["MAE2EL"] *0.9)  #RE2EL= 90% of MAE2EL 
        OE2EL=int(issues[task_id]["OE2EL"])
        #TODO:RE2EL should be defined based on a policy. Now, we only ask a RE2EL= 90% of MAE2EL as a 
        #very basic policy 
     

        return task_id, pes_flag,RE2EL,task_priority, OE2EL,action,app_type,app_part




    #Name:issue_resume_enhanced_edge
    #Implements the algorithm needed to resume a suspended enhanced task with the server in the edge.
    #Parameters: task_id[string], issues[dict]
    #return: 
    # * task_id [str]: the id of the task we will attend
    # * pes_flag [str]: the new decided primary execution site for the task
    # * RE2EL [int]: in case we migrate to a new edge, we request ENIM an edge with <= latency than RE2EL  
    # * task_priority [int]: the priority of the task being attended
    # * OE2EL [int]: the Observed End-to-End Latency
    # * action [str]: the action to be taken
    
    def issue_resume_enhanced_edge(self,task_id,issues):

        loggerDM.info ("ISSUE MANAGEMENT: issue_resume_enhanced_edge case has been selected")
        action="Resume"
        pes_flag="None"
        RE2EL =0
        OE2EL=0
        task_priority=1
        app_type=issues[task_id]["app_type"]
        app_part="client"
        #TODO
        
        return  task_id, pes_flag,RE2EL, task_priority,OE2EL,action, app_type, app_part



    #Name:issue_resume_enhanced_local
    #Implements the algorithm needed to resume a suspended enhanced task with the server local as well.
    #Parameters: task_id[string], issues[dict]
    #return: 
    # * task_id [str]: the id of the task we will attend
    # * pes_flag [str]: the new decided primary execution site for the task
    # * RE2EL [int]: in case we migrate to a new edge, we request ENIM an edge with <= latency than RE2EL  
    # * task_priority [int]: the priority of the task being attended
    # * OE2EL [int]: the Observed End-to-End Latency
    # * action [str]: the action to be taken
    
    def issue_resume_enhanced_local(self,task_id,issues):

        loggerDM.info ("ISSUE MANAGEMENT: issue_resume_enhanced_local case has been selected")
        action="Resume"
        pes_flag="None"
        RE2EL =0
        OE2EL=0
        task_priority=1
        app_type=issues[task_id]["app_type"]
        app_part="client"

        task_priority=issues[task_id]["priority"]
        #TODO: Resume both, client and server locally
        
        return  task_id, pes_flag,RE2EL, task_priority,OE2EL, action, app_type, app_part



    #Name:issue_resume_client_local
    #Implements the algorithm needed to resume a suspended enhanced task with the server local as well.
    #Parameters: task_id[string], issues[dict]
    #return: 
    # * task_id [str]: the id of the task we will migrate (or not)
    # * pes_flag [str]: the new decided primary execution site for the task
    # * RE2EL [int]: in case we migrate to a new edge, we request ENIM an edge with <= latency than RE2EL  
    # * task_priority [int]: the priority of the task being attended
    # * OE2EL [int]: the Observed End-to-End Latency
    # * action [str]: the action to be taken
    
    def issue_resume_client_local(self,task_id,issues):

        loggerDM.info ("ISSUE MANAGEMENT: issue_resume_client_local case has been selected")
        action="Resume"
        pes_flag="None"
        RE2EL =0
        OE2EL=0
        task_priority=1
        app_type=issues[task_id]["app_type"]
        app_part="client"

        #TODO
        #DMCommunication.communicate (self.myDMTIComm, protocol="REST", function="resume task", _task_id_=task_id, _task_type_="client")

        return  task_id, pes_flag,RE2EL, task_priority,OE2EL,action, app_type, app_part

    
    #Name:issue_not_IDLE
    #Implements the algorithm needed to make a decision when there is not enough IDLE time in the UE.
    #Parameters: task_id[string], issues[dict]
    #return: 
    # * task_id [str]: the id of the task we will migrate (or not)
    # * pes_flag [str]: the new decided primary execution site for the task
    # * RE2EL [int]: in case we migrate to a new edge, we request ENIM an edge with <= latency than RE2EL  
    # * task_priority [int]: the priority of the task being attended
    # * OE2EL [int]: the Observed End-to-End Latency
    # * action [str]: the action to be taken
    
    def issue_not_IDLE(self,task_id,issues):

        loggerDM.info ("ISSUE MANAGEMENT: issue_not_IDLE case has been selected")
        action="None"
        pes_flag="None"
        RE2EL =0
        OE2EL=0
        task_priority=1
        app_type=issues[task_id]["app_type"]
        app_part="client"
        
        return  task_id, pes_flag,RE2EL, task_priority,OE2EL, action, app_type, app_part



    #Name:default
    #Implements a default case in case any issue has been detected.
    #Parameters: task_id[string], issues[dict]
    #return: 
    # * task_id [str]: the id of the task we will migrate (or not)
    # * pes_flag [str]: the new decided primary execution site for the task
    # * RE2EL [int]: in case we migrate to a new edge, we request ENIM an edge with <= latency than RE2EL  
    # * task_priority [int]: the priority of the task being attended
    # * OE2EL [int]: the Observed End-to-End Latency
    # * action [str]: the action to be taken
    
    def default(self,task_id,issues):

        loggerDM.info ("ISSUE MANAGEMENT: default case has been selected")
        #print ("issues in default--------------->",task_id, issues)
        action="None"          
        pes_flag="None"
        RE2EL =0
        OE2EL=0
        task_priority=1   
        app_type="local"
        app_part="client"

        #TODO: Implement an algorithm in case there is no issue found 
        #Can we optimize even more the execution of tasks if all of them are running properly?
        #For example, even if there is no issue, we could attempt to migrate an edge-enhanced task to the edge
        #as we assume that any edge-enhanced task will better run at the edge (more quality or features)      
            
        return  task_id, pes_flag,RE2EL , task_priority, OE2EL, action, app_type, app_part



    #Name:decide_worst_issue_to_attend
    #Determines what is the worst issue to be attended from the list of issues received from
    #Task Monitor component only based on task priority. As for now, if both tasks have the same priority,
    #the algorithm takes the task with higher id 
    #Parameters: issues[dict]
    #return: 
    # * task_with_issue_to_attend[string]: task_id of the task to be attended

    def decide_worst_issue_to_attend(self, issues):
        #TODO: this could be improved by using more policies
        loggerDM.debug ("ISSUE MANAGEMENT: Lastest data in  DM-> "+str(issues) )
        worst_issue_dict={} #initializes a dict that will contain all tasks with detected issues

        #iterates through all tasks to determine the worst issue in the system
        for task_id in issues:
            
            #case issue_type !=None and the task has not been attended yet
            #print("********************", issues)
            #print("********************", issues[task_id])
            if issues[task_id]["issue"] != "None" and issues[task_id]["attended"] <= 0:
                worst_issue_dict[task_id]=issues[task_id]["priority"] #accumulates only tasks with issues in a dictionary
        #print ("///////////worst_issue_dict", worst_issue_dict)
        if worst_issue_dict: 
            task_with_issue_to_attend= max(worst_issue_dict, key=worst_issue_dict.get) #gets the task with max priority  
            loggerDM.info ("ISSUE MANAGEMENT: task to attend-> "+str(task_with_issue_to_attend) )

        else:
            #case there are no tasks with issues --> we should
            # run default algorithm. key_word None makes sure of this
            task_with_issue_to_attend="None"
        
        return task_with_issue_to_attend



    #Name:decide_methodology
    #Determines what algorithm to implement based on the issue flag.
    #Parameters: None
    #return:
    # * task_id [str]: the id of the task we will migrate (or not)
    # * pes_flag [str]: the new decided primary execution site of the task
    # * RE2EL [int]: in case we migrate to a new edge, we request ENIM an edge with <= latency than RE2EL
    # * task_priority [int]: the priority of the task to be attended

    def decide_methodology(self,issues, system_issues=[]):

        action="None"
        task_with_issue_to_attend=self.decide_worst_issue_to_attend(issues) #determines the task that has the worst issue in the system, so we can act on it

        if task_with_issue_to_attend!="None": #case there is a task with an issue to be attended
            decide_method_to_apply = getattr(self, issues[task_with_issue_to_attend]["issue"]) #returns the decision method (function) to apply based on the issue flag given                   
        else:
            decide_method_to_apply = getattr(self, "default") #case there is no issue to be attended, we execute default case
        
        #print("ISSUE MANAGEMENT: issues before methodology ", issues )
        task_id, pes_flag,RE2EL, task_priority, OE2EL, action, app_type, app_part=decide_method_to_apply(task_with_issue_to_attend,issues) #implements the method based on certain issue       
        loggerDM.debug ("ISSUE MANAGEMENT: case has been applied on "+ str(task_id)+ " with resolution "+ str(pes_flag) + " with RE2EL: "+str(RE2EL) )
        
        return task_id, pes_flag, RE2EL, task_priority, OE2EL, action, app_type, app_part


    
    #Name:decide_methodology_without_ENIM
    #Main method to make and implement a decision based on latest available issues_data when
    # connection to ENIM cannot be reached.
    #Parameters: issues[dict], task_id[str]
    #return: pes_flag [str]

    def decide_methodology_without_ENIM(self, issues, task_id):
        if issues[task_id]["app_type"]=="native": #edge-native tasks can only run at the edge
            # thus, if there is no connection with ENIM, there is nothing else we can do
            pes_flag="hold_pes_flag"
            #TODO: Suspend native client to release resources of a task in dummy-pooling mode
        elif issues[task_id]["app_type"]=="enhanced": #we attempt to run the edge-enhanced task locally
            pes_flag="local_pes_flag"
            #TODO: improve algorithm also this must be related with available resources
            # in case it is not possible to run it locally, suspend both, client and server
        #case task is local, and no connection to ENIM, there is nothing we can do
        else:
             pes_flag="hold_pes_flag"

        loggerDM.debug ("ISSUE MANAGEMENT: as connection with ENIM cannot be reached, task "+ str(task_id)+ " will: "+ str(pes_flag) )
        
        return pes_flag



    #Name:decide_continue_or_regret
    #Once a new node has been requested to ENIM, it decides if the task is to be (or not) migrated to the
    # suggested edge node based on policies. As for now, main decision is based on EE2EL<RE2EL
    #Parameters: solved_supplicant_info[str],latest_issues_info[str], client_id[str]
    #return: 
    # * task_id [str]: the id of the task to migrate
    # * edge_node_IP [str]: the IP of the edge node, to which the application is to be migrated

    def decide_continue_or_regret(self, solved_supplicant_info, latest_issues_info, client_id):

        loggerDM.info ("SUPPLICANT MANAGEMENT: solved supplicant info->"+ str(solved_supplicant_info))
        tolerance_threshold=0.1 #accept a 10% of tolerance
        drop_connection=False        
        s_id=solved_supplicant_info["id"]     
        RE2EL=solved_supplicant_info["RE2EL"]
        OE2EL=solved_supplicant_info["OE2EL"]
        EE2EL=solved_supplicant_info["EE2EL"]
        task_id=solved_supplicant_info["task_id"]
        edge_node_IP=solved_supplicant_info["IP"]
        action="Hold"
        app_type=latest_issues_info[task_id]["app_type"]
        app_part="client"

        #Validate if ENIM purposes a node
        if edge_node_IP !="None":
            if EE2EL<=RE2EL:
                pes_flag="new_edge_pes_flag"
                action="Migrate"
            else:
                OE2EL=latest_issues_info[task_id]["OE2EL"] #to get the latest available OE2EL

                if EE2EL*(1+tolerance_threshold)<OE2EL:
                #case the expected latency is not the requested but is still better than what we 
                #currently have
                    pes_flag="new_edge_pes_flag"
                    action="Migrate"

                else:
                    #Drop ENIM connection. what ENIM suggests is not useful
                    drop_connection=True

                    if latest_issues_info[task_id]["app_type"]=="native":
                        #if it is a native task, there is nothing we can do
                        pes_flag="hold_pes_flag"
                        edge_node_IP="NULL"
                        action="Hold"
                        
                    else:
                        #can only be enhanced
                        #check first what is the current pes, so we can decide
                        if latest_issues_info[task_id]["pes"]=="pes_edge":
                            #if the task is running at the edge, bring it back local
                            pes_flag="local_pes_flag"
                            edge_node_IP="127.0.0.1:1234"
                            action="Migrate"
                            

                        else:
                            #only pes_local is possible
                            #This means: there is no good edge node and I have also a local bad performance
                            #thus, there is nothing we could do
                            pes_flag="hold_pes_flag"
                            edge_node_IP="NULL"
                            action="Hold"
                            
        else:
        #case ENIM did not purpose a node to connect to or did not answered 
            #if task is native or enhanced   
            if latest_issues_info[task_id]["app_type"]=="native" or latest_issues_info[task_id]["app_type"]=="enhanced":
                if OE2EL>latest_issues_info[task_id]["MAE2EL"]:
                    loggerDM.info ("TASK MANAGEMENT: suspend task as it has TIMEOUT->"+ str(task_id))
                    action="Suspend"
                    #DMCommunication.communicate (self.myDMSIComm, protocol="REST", function="suspend task", _task_id_=task_id, _task_type_=latest_issues_info[task_id]["app_type"])
                else:
                    loggerDM.info ("TASK MANAGEMENT: do NOT suspend task as it DOES NOT HAVE TIMEOUT->"+ str(task_id))
                    action="Hold"
            pes_flag="hold_pes_flag"
            


        return task_id,edge_node_IP,pes_flag, drop_connection,action,app_type,app_part
        #task_id, pes_flag,RE2EL,task_priority, OE2EL,action,app_type,app_part




class TaskMonitorAPI ():

    myDMTMComm=DMCommunication.DecisionMakerTaskMonitorCommunication() #creates a common object for the class to be
    #used to implement communicaation with other components



    def __init__(self):

        pass



    #Name:comm_get_issues_from_TaskMonitorAPI
    #obtains the latest list of detected issues by TaskMonitor Component
    #case we use REST, it sends a GET request to the DM REST Server
    #case we use OOP, it directly asks TaskMonitor Component
    #Parameters: None
    #return: issues [dict]   
    #NOTE: DecisionMaker Component works with latest available issues_data in a loop
    
    def comm_get_issues_from_TaskMonitorAPI(self):
        
        issues= DMCommunication.communicate (self.myDMTMComm, protocol="REST", function="get issues") #UNCOMMENT to use REST
        #issues= DMCommunication.communicate (self.myDMTMComm, protocol="OOP", function="get issues") #UNCOMMENT to use OOP
        #TODO: Validate if issues are in the right fromat before returning them
        for task_id in issues["task_info"]:
            issues["task_info"][task_id]["attended"] = 0
                                   
        return issues



    #Name:comm_set_issues_from_TaskMonitorAPI
    #sets the latest list of detected issues by TaskMonitor Component
    #case we use REST, it sends a POST request to the DM REST Server
    #case we use OOP, it directly asks TaskMonitor Component
    #Parameters: None
    #return: issues [dict]
    #NOTE: DecisionMaker Component works with latest available issues_data in a loop
    
    def comm_set_issues_from_TaskMonitorAPI(self,issues):       

        issues= DMCommunication.communicate (self.myDMTMComm, protocol="REST", function="set issues",_data_=issues) #UNCOMMENT to use REST
        #issues= DMCommunication.communicate (self.myDMTMComm, protocol="OOP", function="set issues",_data_=issues) #UNCOMMENT to use OOP
        #TODO: Validate if issues are in the right fromat before returning them

        return issues



    #Name:comm_clean_issues_from_TaskMonitor
    #cleans the list of detected issues in TaskMonitor Component
    #Parameters: None
    #return: issues [dict] (clean)
    #NOTE: In practice we wont use this method as issues_data will update whenever taskMonitor component sends
    #new data. DecisionMaker Component works with latest available issues_data in a loop. thus, we dont need to clean
    #any data in TaskMonitor Component as it will update/clean the issues_data itself

    def comm_clean_issues_from_TaskMonitor(self):

        issues= DMCommunication.communicate (self.myDMTMComm, protocol="OOP", function="clean issues")
        #issues= DMCommunication.communicate (self.myDMTMComm, protocol="REST", function="clean issues")

        return issues





class TaskInterfaceAPI ():

    myDMTIComm=DMCommunication.DecisionMakerTaskInterfaceCommunication() #creates a common object for the class to be



    def __init__(self):

        pass



    #Name:set_pes
    #Send a notification to the tasks interface component to tell which task is to 
    # be migrate to what primary execution site
    #Parameters: task_id[str], pes[str], edge_ip[str]
    #return: None

    def set_pes(self,task_id, pes, edge_ip):

        #DMCommunication.communicate (self.myDMTIComm, protocol="OOP", function="migrate task", _task_id_=task_id, _pes_=pes, _edge_ip_=edge_ip) 
        DMCommunication.communicate (self.myDMTIComm, protocol="REST", function="migrate task", _task_id_=task_id, _pes_=pes, _edge_ip_=edge_ip) 
        #TODO: when migrating a server, in case the app is enhanced, we should suspend the local server task
        error_setting_pes=False

        return error_setting_pes





class SchedulerInterfaceAPI ():



    def __init__(self):

        self.myDMSIComm=DMCommunication.DecisionMakerSchedulerInterfaceCommunication() #creates a common object for the class to be
        #used to implement communication with other components
        
    #TODO: implement here the function suspend task. Now, DecisionHandler is directly invoking DMCommunication, but the request must go throug
    # SchedulerInterfaceAPI before

    #Name:suspendTask
    #Send a notification to the scheduler interface component to tell which task is to 
    # be suspended
    #Parameters: task_id[str], task_type[str] (local/enhanced/native)
    # return: None

    def suspendTask(self, task_id, task_type):
        DMCommunication.communicate (self.myDMSIComm, protocol="REST", function="suspend task", _task_id_=task_id, _task_type_=task_type)



    #Name:resumeTask
    #Send a notification to the scheduler interface component to tell which task is to 
    # be resumed
    #Parameters: task_id[str], pes[str], edge_ip[str]
    #return: None

    def resumeTask(self, task_id, task_part):
        DMCommunication.communicate (self.myDMSIComm, protocol="REST", function="resume task", _task_id_=task_id, _task_type_=task_part)




class ECMAPI ():

    myDMECMComm=DMCommunication.DecisionMakerECMCommunication() #creates a common object for the class to be
    #used to implement communication with other components
    
    
    
    def __init__(self):
        self._key_lock = threading.Lock()



    #Name:open_supplicant
    #Once validation has been performed, asks ECM Component to open a supplicant in order to get a new edge node for a certain task
    #Parameters: supplicant_id[int],task_id[str], task_times_to_ask[int], task_hold_time[int], RE2EL[int]
    #return: None

    def open_supplicant(self,supplicant_id, task_id, task_times_to_ask=1, task_hold_time=1, RE2EL=0, OE2EL=0):
        
        #error_oppening=DMCommunication.communicate (self.myDMECMComm, protocol="OOP", function="open supplicant", _ask_times_=task_times_to_ask, 
        #_hold_time_=task_hold_time, _RE2EL_=RE2EL, _supplicant_id_=supplicant_id, _task_id_=task_id)

        error_oppening=DMCommunication.communicate (self.myDMECMComm, protocol="REST", function="open supplicant", _ask_times_=task_times_to_ask, 
        _hold_time_=task_hold_time, _RE2EL_=RE2EL, _supplicant_id_=supplicant_id, _task_id_=task_id,_OE2EL_=OE2EL)
        
 
        return error_oppening



    #Name:cancel_supplicant
    #asks ECM Component to cancel the execution of a supplicant and set status=CANCELED in supplicantsregistry
    #Parameters: supplicant_id[int]
    #return: None

    def cancel_supplicant(self,supplicant_id):

        error_cancelling=DMCommunication.communicate (self.myDMECMComm, protocol="OOP", function="cancel supplicant", _supplicant_id_=supplicant_id)
        #error_cancelling=DMCommunication.communicate (self.myDMECMComm, protocol="REST", function="cancel supplicant", _supplicant_id_=supplicant_id)



    #Name:complete_supplicant
    #asks ECM Component to set the estatus of a supplicant as completed in supplicantsregistry
    #Parameters: supplicant_id[int]
    #return: None

    def complete_supplicant(self,supplicant_id):

        error=DMCommunication.communicate (self.myDMECMComm, protocol="OOP", function="complete supplicant", _supplicant_id_=supplicant_id)
        #error=DMCommunication.communicate (self.myDMECMComm, protocol="OOP", function="complete supplicant", _supplicant_id_=supplicant_id)



    #Name:cancel_active_supplicants_to_start
    #makes sure there is no supplicant set as "active" in the database when the DMComponent boots, so it can have a 
    # fresh beginning
    #Parameters: None
    #return: None

    def cancel_active_supplicants_to_start(self):

        related_supplicants_from_registry=self.get_related_supplicants_from_registry("t1", "one_at_the_time")
        if related_supplicants_from_registry:
            if len(related_supplicants_from_registry)>0:
                
                for supplicant_registry in related_supplicants_from_registry:
                    #iterate through each "garbage" supplicant and set it to CANCELED
                    loggerDM.debug("SUPPLICANT MANAGEMENT: cancelling garbage supplicant(s)")
                    self.cancel_supplicant(supplicant_registry[0])
        else:
            loggerDM.debug("SUPPLICANT MANAGEMENT: starting with a clean registry")        
                    


    #Name:manage_supplicants_based_on_policy
    #first validates if the supplicant to be created already exists or is a new supplicant 
    #and determines whether to create it or not based on a given policy. 
    #also, this method has the ability to CANCEL a supplicant based on the same policy
    #Parameters: task_id[str],task_times_to_ask[int], task_hold_time[int], RE2EL[int],supplicant_type_policy_name[str]
    #supplicant_type_policy_name can be:
    #* one_per_task: the system allows to have only one supplicant open per task at the time (in parallel)
    #  but there could be several supplicants at the same time attending different tasks
    #* one_at_the_time: the system allows to have only one supplicant running at the time (independently of the task it aims to attend)
    #return: None

    def manage_supplicants_based_on_policy(self,task_id,task_times_to_ask, task_hold_time, RE2EL,supplicant_type_policy_name='one_per_task',OE2EL=0):
        
        error_oppening= False
        #gets the active supplicants of all or a certain task (depending on supplicant_type_policy_name) from the supplicantregistry
        related_supplicants_from_registry=self.get_related_supplicants_from_registry(task_id, supplicant_type_policy_name)
        loggerDM.debug("SUPPLICANT MANAGEMENT: related supplicant data-> "+str(related_supplicants_from_registry) )
        open_flag=True
        #case there is one or more supplicants running at the same time
        if len(related_supplicants_from_registry)>0:

            for supplicant_registry in related_supplicants_from_registry:
                #iterate through each supplicant and check if it has the same parameters as the one we aim to open
                if supplicant_registry[1]==task_id and int(supplicant_registry[5])==int(task_hold_time) and int(supplicant_registry[6])==int(task_times_to_ask) and int(supplicant_registry[8])==int(RE2EL):
                    loggerDM.debug("SUPPLICANT MANAGEMENT: attemping to open the exact same supplicant")
                    open_flag=False
                    
                #we try to open a supplicant with new parameters, thus, we cancel previous supplicants before opening a new one
                else:
                    loggerDM.debug("SUPPLICANT MANAGEMENT: cancelling previous supplicant(s) and openning a new one")
                    self.cancel_supplicant(supplicant_registry[0])
                    loggerDM.debug("SUPPLICANT MANAGEMENT: supplicant_registry-> "+ str(supplicant_registry))              
                    
        if open_flag:
            # creates a "unique" id for the new supplicant
            #supplicant_id=self.mysupplicantmanager.generate_supplicant_id() #keep in case we after want to create our
            #own supplicant_id again. In case yes, all methods still use parameter supplicant_id, but SQL table must be changed
            #as for now, the sqlite table auto_increments the value of supplicant_id, thus, this option is disabled
            #and set supplicant_id parameter set to '0'. 
            error_oppening=self.open_supplicant(55,task_id,task_times_to_ask, task_hold_time, RE2EL, OE2EL) #there is no other supplicant trying to attend the same task, thus, we must create one directly
            #TODO: what to do if there is an error openning the supplicant
            loggerDM.debug("SUPPLICANT MANAGEMENT: open supplicant for task: " + str(task_id) + "task_times_to_ask" + str(task_times_to_ask) + "task_hold_time"+ str(task_hold_time) + "RE2EL" + str(RE2EL))
        
        return error_oppening
                

       
    #Name:get_related_supplicants_from_registry
    #get all supplicants that satisfy the condition established by the policy from supplicantregistry (DB) 
    #it communicates with ECM component in order to get this information
    #Parameters: task_id[str],supplicant_type_policy_name[str]
    #supplicant_type_policy_name can be:
    #* one_per_task: the system allows to have only once supplicant open per task at the time (in parallel)
    #  but there could be several supplicants at the same time attending different tasks
    #* one_at_the_time: the system allows to have ONLY one supplicant running at the time (independently of the task it aims to help)
    #return: None

    def get_related_supplicants_from_registry(self,task_id,supplicant_type_policy_name):

        related_supplicants_from_registry=DMCommunication.communicate (self.myDMECMComm, protocol="OOP", function="get related supplicant", _task_id_=task_id,_policy_name_=supplicant_type_policy_name)
        #related_supplicants_from_registry=DMCommunication.communicate (self.myDMECMComm, protocol="REST", function="get related supplicant", _task_id_=task_id,_policy_name_=supplicant_type_policy_name)
        
        return related_supplicants_from_registry



    #Name:get_supplicant_by_id
    #returns the data of certain supplicant with a given ID
    #Parameters: supplicant_id[int]
    #return: related_supplicants_from_registry [dict]

    def get_supplicant_by_id (self, supplicant_id):

        related_supplicants_from_registry=DMCommunication.communicate (self.myDMECMComm, protocol="OOP", function="get supplicant by id", _supplicant_id_=supplicant_id)
        
        return related_supplicants_from_registry



    #Name:drop_suggested_match
    #notifies ENIM that the suggested match won´t be accepted
    #Parameters: client_id[int]
    #return: None

    def drop_suggested_match(self, client):

        error_dropping=DMCommunication.communicate (self.myDMECMComm, protocol="OOP", function="drop connection", _client_id_=client)
        #error_dropping=DMCommunication.communicate (self.myDMECMComm, protocol="REST", function="drop connection", _client_id_=client)





class DecisionMakerEngine ():

    _instance = None



    #Name:getInstance
    #returns the singleton object
    #Parameters: None
    #return: _instance[object]

    def getInstance():

        if DecisionMakerEngine._instance == None:
            DecisionMakerEngine()

        return DecisionMakerEngine._instance



    #constructor
    #Applies singleton, so we can only create one object of DecisionMakerEngine class
    #The object of DecisionMakerEngine class in turn creates objects of all other classes of the component
    #to be able to interact with them. All incomming or outgoing information goes through DecisionMakerEngine

    def __init__(self, default_param= {'task_info': {'t1': {'id': 't1', 'OE2EL': 1, 'state': 'BLOCKED', 'priority': '2', 'app_type': 'enhanced', 'MAE2EL': 250, 'resources_client': 10, 
                'resources_server': 10, 'QR': 5, 'pes': 'pes_local', 'issue': 'None'}},
                 'resources': {'available': 100, 'used': 0}, 'system_issues': []}):

        if DecisionMakerEngine._instance != None:
            raise Exception("Singleton: there can only be one object")
        else:
            DecisionMakerEngine._instance = self
            self.DME_queue= Queue(maxsize = 3)           
            self.myDecisionHandler=DecisionHandler()
            self.myTaskMonitorAPI=TaskMonitorAPI ()
            self.myTaskInterfaceAPI=TaskInterfaceAPI()
            self.mySchedulerInterfaceAPI=SchedulerInterfaceAPI()
            self.myECMAPI=ECMAPI()
            self._default_issues_data=default_param
            self._my_latest_issues=default_param
            self._key_lock = threading.Lock()
            self.attended_score_manager=AttendedScoreManager("priority")
            self.attended_score_task_values={} 



    #Name:get_issues_data
    #returns issues data from the DM REST server.
    #Parameters: None
    #return: issues [dict]
     
    def get_issues_data(self):

        try:
            issues=self.myTaskMonitorAPI.comm_get_issues_from_TaskMonitorAPI()
            if issues:
                return issues
        except Exception as e:
            pass
            #print(e)

        return self._default_issues_data
        


    #Name:set_issues_data_in_server
    #sets issues data in the DM REST Server.
    #Parameters: issues_data[dict]
    #return: request_response: 
    # * case no errors --> server returns the same issues_data
    # * case erros --> "NULL"

    def set_issues_data_in_server(self,issues_data ):

        try:
            request_response=self.myTaskMonitorAPI.comm_set_issues_from_TaskMonitorAPI(issues_data)              
        except Exception as e:
            request_response="NULL"
            #print(e)

        return request_response



    #Name:apply_decision_methodology
    #Main method to make and implement a decision based on latest available issues_data.
    #Parameters: None
    #return: None

    def apply_decision_methodology(self):
        attempts_to_connect=0 
        max_attempts_to_connect=3 
        self.set_issues_data_in_server(self._default_issues_data)

        while True:      
            
            self._key_lock.acquire() #locks the resources
            self._my_latest_issues=self.get_issues_data() #reads latest available _issues_data

            #once resource issues has been considered, check for attended score
            for task_id in self._my_latest_issues["task_info"]:
                #loggerDM.debug ("ATTENDED SCORE: Setting score for " + str(task_id) )
                try:
                    
                    score=self.attended_score_manager.decreaseAttendedScore(self.attended_score_task_values[task_id],1)
                    self.attended_score_task_values[task_id]=score
                    self._my_latest_issues["task_info"][task_id]["attended"] = score
                    loggerDM.debug ("ISSUE MANAGEMENT: assigned score " + str(score) )
                except Exception as e:
                    #loggerDM.debug ("ATTENDED SCORE: there is no attended registered score yet for " + str(task_id) )
                    try:
                        #loggerDM.debug ("ATTENDED SCORE: unable to decrease attended score as " + str(task_id) + " has not been attended yet" )
                        score=self.attended_score_manager.decreaseAttendedScore(self._my_latest_issues["task_info"][task_id]["attended"],1)
                        #loggerDM.debug ("ATTENDED SCORE: assigned score " + str(score) )
                    except Exception as e: 
                        #loggerDM.debug ("ATTENDED SCORE: registering new score for " + str(task_id)) 
                        self.attended_score_task_values[task_id]=0   
                        #loggerDM.debug ("ATTENDED SCORE: assigned score " + str(0) )    


            loggerDM.debug("ISSUE MANAGEMENT:Data before setting resource issues: " + str(self._my_latest_issues))

            #firstly detect if there is a resource related issue in the system
            for system_issue in self._my_latest_issues["system_issues"]:
                if (system_issue == "issue_resources"):
                    self.checkSystemResources()
             

                elif (system_issue == "issue_task_suspended"):
                    pass
                    #in case we need to do something before

            loggerDM.debug("RESOURCES MANAGEMENT:Final data: " + str(self._my_latest_issues["task_info"])) 




            #Apply any of the programmed methodologies based on the issue type                        
            task_id, pes_flag, RE2EL,task_priority,OE2EL, action, app_type, app_part=self.myDecisionHandler.decide_methodology(self._my_latest_issues["task_info"], self._my_latest_issues["system_issues"]) #takes a decision and determines in which task
            self._key_lock.release()

            #Each metodology returns an action to be taken thus, we must act based on that
            if action =="Suspend":
                #set attended score to its max based on priority policy
                self.mySchedulerInterfaceAPI.suspendTask(task_id,app_type)
                score=self.attended_score_manager.setPolicyBasedScore(_priority_=task_priority)
                self.attended_score_task_values[task_id]=score
                #methodology already suspends the task
                loggerDM.info ("ISSUE MANAGEMENT: Issue resolution-> The task has been suspended")
            elif action== "Resume":
                #set attended score to its max based on priority policy
                self.mySchedulerInterfaceAPI.resumeTask(task_id,app_part)
                score=self.attended_score_manager.setPolicyBasedScore(_priority_=task_priority)
                self.attended_score_task_values[task_id]=score
                #methodology already resumes the task
                loggerDM.info ("ISSUE MANAGEMENT: Issue resolution-> The task has been resumed")
            
            elif action== "Hold":
                #set attended score to its max based on priority policy
                score=self.attended_score_manager.setPolicyBasedScore(_priority_=task_priority)
                self.attended_score_task_values[task_id]=score
                loggerDM.info ("ISSUE MANAGEMENT: Issue resolution-> There is no possible action to be taken")
                #TODO

            elif action== "Migrate":
                loggerDM.info ("ISSUE MANAGEMENT: Issue resolution-> Migrating a task")
                #case decision is to connect to a new edge node, we must ask ENIM
                if pes_flag == "new_edge_pes_flag":
                    #POLICY_CHANGE: one_per_task, one_at_the_time
                    error_oppening=self.open_supplicant_with_policy(task_id,task_priority, RE2EL,"priority_request_edge_policy","one_at_the_time", OE2EL)
                    if error_oppening:
                        loggerDM.info ("ISSUE MANAGEMENT: ENIM has not replied. Attempting again")
                        attempts_to_connect+=1
                    
                    if attempts_to_connect> max_attempts_to_connect:
                        #TODO: the method decide_methodology_without_ENIM is not fully implemented
                        loggerDM.info ("ISSUE MANAGEMENT: ENIM has not replied. Making a desicion without ENIM")
                        pes_flag=self.myDecisionHandler.decide_methodology_without_ENIM(self._my_latest_issues["task_info"], task_id) #carefull might have race conditions here --> mutex
                        self.switch_pes(task_id,pes_flag,"NULL","NULL")
                #here we dont set the attended score as it will be done once the system receives a response from ENIM and the supplicant is closed

                elif pes_flag== "hold_pes_flag":
                    #set attended score to its max based on priority policy
                    score=self.attended_score_manager.setPolicyBasedScore(_priority_=task_priority)
                    self.attended_score_task_values[task_id]=score
                    
                elif pes_flag== "local_pes_flag":
                    #set attended score to its max based on priority policy
                    score=self.attended_score_manager.setPolicyBasedScore(_priority_=task_priority)
                    self.attended_score_task_values[task_id]=score
                    #TODO Implement communication to migrate the server local
                else:
                    loggerDM.info ("ISSUE MANAGEMENT: Issue resolution-> nothing to do")
            else:
                loggerDM.info ("ISSUE MANAGEMENT: Issue resolution-> No defined action")

            time.sleep(TIME_ITERATION_DECISION_MAKER_MS/1000)


    def checkSystemResources(self):
        r_available= self._my_latest_issues["resources"]["available"]
        r_used= self._my_latest_issues["resources"]["used"]

        #case we have available resources, then we can check if there is a task that can be resumed 
        if (r_available>r_used):
            loggerDM.debug("RESOURCES MANAGEMENT: Attempting to resume a suspended tasks as there are available resources")
            for task_id in self._my_latest_issues["task_info"]:
                required_resources_client=0
                required_resources_server=0
                #case there is a suspended task that can be resumed (if there are available resources)
                if  (self._my_latest_issues["task_info"][task_id]["state"] == "SUSPENDED"):
                    loggerDM.debug("RESOURCES MANAGEMENT:There is a suspended task: " + str(task_id) )
                    required_resources_client=self._my_latest_issues["task_info"][task_id]['resources_client']
                    #case we have enough available resources to resume the client
                    if (r_available>=r_used+required_resources_client):
                        self._my_latest_issues["task_info"][task_id]['issue']="issue_resume_client_local"
                        loggerDM.debug("RESOURCES MANAGEMENT: we have local resources to resume the client of: " + str(task_id) )
                        if  (self._my_latest_issues["task_info"][task_id]["app_type"] == "enhanced"):
                            required_resources_server=self._my_latest_issues["task_info"][task_id]['resources_server']
                            #check if we can also resume the server of a enhanced task
                            if r_used+required_resources_client + required_resources_server <r_available:
                                loggerDM.debug("RESOURCES MANAGEMENT: we have local resources to resume the server of: " + str(task_id) )
                                self._my_latest_issues["task_info"][task_id]['issue']="issue_resume_enhanced_local"
                            else:
                                self._my_latest_issues["task_info"][task_id]['issue']="issue_resume_enhanced_edge"
                                loggerDM.debug("RESOURCES MANAGEMENT: we can only resume the client locally and server at the edge of: "+ str(task_id) )
                        elif  (self._my_latest_issues["task_info"][task_id]["app_type"] == "native"):
                            self._my_latest_issues["task_info"][task_id]['issue']="issue_resume_native"
                else:      
                    #loggerDM.debug("RESOURCES MANAGEMENT: Task is not suspended: " +str(task_id) )
                    pass

        #case (for some reason) the tasks are using more resources than the available        
        elif (r_available<r_used): 
            #we need to suspend low-priority tasks
            for task_id in self._my_latest_issues["task_info"]:
                self._my_latest_issues["task_info"][task_id]['issue']="issue_no_enough_resources"      


    #Name:open_supplicant_with_policy
    #Implements a policy to forward the supplicant request to ECMAPI with the required parameters.
    #Parameters: task_id[str],task_priority[int],RE2EL[int], request_policy_name[str], supplicant_type_policy_name[str]
    #request_policy_name is used to determine the number of times the supplicant will ask for a node and the time 
    # it waits between requests. It can be:
    #* priority_request_edge_policy: task_times_to_ask=task_priority and task_hold_time=task_priority
    #supplicant_type_policy_name determines the way supplicants will be handled. It can be:
    #* one_per_task: the system allows to have only once supplicant open per task at the time (in parallel)
    #  but there could be several supplicants at the same time attending different tasks
    #* one_at_the_time: the system allows to have ONLY one supplicant running at the time (independently of the task it aims to help)
    #return: None

    def open_supplicant_with_policy(self,task_id,task_priority,RE2EL, request_policy_name, supplicant_type_policy_name,OE2EL=0):

        #Applies the given policy to determine the number of times we will request ENIM for a match making
        #and the time we will wait inbetween requests
        task_times_to_ask, task_hold_time=self.apply_request_policy(task_priority, request_policy_name)
        
        #validates, cancels previous supplicants (if needed), and open a new one (if needed)
        error_oppening=self.myECMAPI.manage_supplicants_based_on_policy(task_id,task_times_to_ask, task_hold_time, RE2EL,supplicant_type_policy_name, OE2EL)     
        loggerDM.debug("SUPPLICANT MANAGEMENT: Supplicant data: " +str(task_id) + " task_priority "+str(task_priority)+ " policy_name: " + str(request_policy_name))
        return error_oppening


    

    #Name:apply_request_policy
    #Implements a policy to determine the times we will ask ENIM for a new edge node
    # and the time we will wait between requests.
    #Parameters: task_priority [int], policy_name [str]
    #return: 
    # * task_times_to_ask [int]: the max number of times we will ask ENIM for a new edge node
    # * task_hold_time [int]: The time (in seconds) we will wait in between each attempt
    #TODO: create more and better policies

    def apply_request_policy(self,task_priority, policy_name):

        if policy_name=="priority_request_edge_policy":
            #case i have priority 1, i only ask one time for a new edge, 
            #case i have priority 2, i ask 2 times for a new edge node and wait 
            #2 seconds in between both requests
            #case i have priority 3, i ask 3 times for a new edge node and wait 
            #3 seconds in between the requests
            task_times_to_ask=task_priority
            task_hold_time=task_priority
        
        return task_times_to_ask, task_hold_time



    #Name:switch_pes
    #implements the primary execution site switch after a final decision has been taken.
    #Parameters: task_id[str],pes_flag[str],RE2EL[int], edge_IP[str], supplicant_id [int]
    #return:

    def switch_pes(self, task_id,pes_flag,edge_IP,supplicant_id):

        error_setting_pes=self.myTaskInterfaceAPI.set_pes(task_id,pes_flag,edge_IP)

        if not error_setting_pes:                     
            if supplicant_id !="NULL":
                error_setting_pes=self.myECMAPI.complete_supplicant(supplicant_id)
                
                if not error_setting_pes:
                    loggerDM.debug ("SUPPLICANT MANAGEMENT:supplicant completed-> "+ str(supplicant_id))
        
        return error_setting_pes                 

            


    #Name:ECM_listener
    #implements listener_supplicant_response.
    #Parameters: None
    #return: None

    def ECM_listener(self):

        while True:
            data_supplicant=self.DME_queue.get()
            #TODO: could validate if the supplicant has not been canceled meanwhile
            #this can rarely happen, as if we set the supplicant to CANCEL, we will kill
            #the supplicant thread as well and thus it cannot return an answer
            #the only chance is that the exact moment we CANCEL, the supplicant
            #gets a response from ENIM
            client_id=data_supplicant["client_id"]
            data=data_supplicant["supplicants"]
            self._key_lock.acquire() #locks the resources        
            latest_issues=self._my_latest_issues["task_info"]
            self._key_lock.release()

            
            #iterates through all solved supplicants
            for solved_supplicant in data:
                supplicant_id=solved_supplicant["id"]
                #as system state could have changed until the supplicant was solve, it implements an algorithm to decide what to do with the available information
                task_id,edge_node_IP,pes_flag, drop_connection,action,app_type,app_part=self.myDecisionHandler.decide_continue_or_regret(solved_supplicant,latest_issues,client_id)
                
                loggerDM.info ("ISSUE MANAGEMENT: decided primary execution site-> "+ str(pes_flag))
                loggerDM.info ("ISSUE MANAGEMENT: task->"+ str(task_id) + " nodeIP-> "+ str(edge_node_IP))
                loggerDM.info ("ISSUE MANAGEMENT: check if task" + str(task_id)+ " is suspended "+ str(latest_issues))
                
                #case the suggested match is not accepted by the system
                if drop_connection:
                    self.myECMAPI.drop_suggested_match(client_id)

                self._key_lock.acquire() #locks the resources    

                #Each metodology returns an action to be taken thus, we must act based on that
                if action =="Suspend":
                    #set attended score to its max based on priority policy
                    self.mySchedulerInterfaceAPI.suspendTask(task_id,app_type)
                    score=self.attended_score_manager.setPolicyBasedScore(_priority_=latest_issues[task_id]["priority"])
                    self.attended_score_task_values[task_id]=score
                    #methodology already suspends the task
                    loggerDM.info ("ISSUE MANAGEMENT: Issue resolution After Decide Continue or Regret-> The task has been suspended")
                elif action== "Resume":
                    #set attended score to its max based on priority policy
                    self.mySchedulerInterfaceAPI.resumeTask(task_id,app_part)
                    score=self.attended_score_manager.setPolicyBasedScore(_priority_=latest_issues[task_id]["priority"])
                    self.attended_score_task_values[task_id]=score
                    #methodology already resumes the task
                    loggerDM.info ("ISSUE MANAGEMENT: Issue resolution After Decide Continue or Regret-> The task has been resumed")
                
                elif action== "Hold":
                    #set attended score to its max based on priority policy
                    score=self.attended_score_manager.setPolicyBasedScore(_priority_=latest_issues[task_id]["priority"])
                    self.attended_score_task_values[task_id]=score
                    loggerDM.info ("ISSUE MANAGEMENT: Issue resolution After Decide Continue or Regret-> There is no possible action to be taken")
                    #TODO

                elif action== "Migrate":
                    loggerDM.info ("ISSUE MANAGEMENT: Issue resolution After Decide Continue or Regret-> Migrating a task")

                    if pes_flag != "hold_pes_flag":
                        loggerDM.info ("ISSUE MANAGEMENT: After Decide Continue or Regret check if task" + str(task_id)+ " is suspended "+ str(latest_issues))

                        if (latest_issues[task_id]["state"]=="SUSPENDED"):
                            loggerDM.debug("TASK MANAGEMENT :resume task before migrating it: " + str(task_id))
                            self.mySchedulerInterfaceAPI.resumeTask(task_id,"client")
                            #DMCommunication.communicate (self.myDMTIComm, protocol="REST", function="resume task", _task_id_=task_id, _task_type_="client")
                            #TODO: release the client of the task
                        #TODO: enable switch_pes to migrate back local
                        error_setting_pes=self.switch_pes(task_id,pes_flag,edge_node_IP,supplicant_id)
                        #in this case, the supplicant is set to completed in set pes function
                        if not error_setting_pes:
                              
                            #set attended score to the max value based on its priority 
                            score=self.attended_score_manager.setPolicyBasedScore(_priority_=latest_issues[task_id]["priority"])
                            self.attended_score_task_values[task_id]=score
                            
                    else:                    
                        
                        #set attended score to the max value based on its priority 
                        score=self.attended_score_manager.setPolicyBasedScore(_priority_=latest_issues[task_id]["priority"])
                        self.attended_score_task_values[task_id]=score
                        
                        #self.set_issues_data_in_server(self._my_latest_issues)
                        error_setting=self.myECMAPI.complete_supplicant(supplicant_id)

                        if not error_setting:
                            loggerDM.info ("SUPPLICANT MANAGEMENT:  supplicant process completed "+ str(supplicant_id))
                        else:
                            loggerDM.error ("SUPPLICANT MANAGEMENT:  error completing supplicant process "+ str(supplicant_id))

                else:
                    loggerDM.info ("ISSUE MANAGEMENT: Issue resolution After Decide Continue or Regret->  No defined action")

                self._key_lock.release()






#Defines the REST Server of the DM component

app=Flask(__name__)
issues_data_new= {} 
supplicant_update={}

@app.route('/')
def home():

    return "hello from DM Server"



@app.route('/dm/tm/latest_issues')
def get_latest_issue():

    #TODO: This should have a mutex as it could happen at the same time when someone is writing the variable
    
    return jsonify(issues_data_new)



@app.route('/dm/tm/latest_issues', methods=['POST'])
def set_latest_issue():
    
    issues_data=request.get_json()
    issues_data_new["task_info"]=issues_data["task_info"]
    issues_data_new["resources"]=issues_data["resources"]
    issues_data_new["system_issues"]=issues_data["system_issues"]
    #TODO: This should have a mutex as it could happen at the same time when someone is reading the variable 
    loggerDM.info ("INCOMMING NOTIFICATION: TM Component has notified-> "+ str(issues_data_new))
    loggerDataLogger.info(str(issues_data_new))
    return jsonify(issues_data_new)



@app.route('/dm/ecm/supplicant_update')
def get_latest_supplicant():
    
    return jsonify(supplicant_update)



@app.route('/dm/ecm/supplicant_update', methods=['POST'])
def set_latest_supplicant():
    obj3= DecisionMakerEngine.getInstance()
    supplicant_update=request.get_json()
    obj3.DME_queue.put(supplicant_update)
    
    return jsonify(supplicant_update)




if __name__ == '__main__':
    obj=DecisionMakerEngine()#sets _issues_data to default param to get the system started
    obj.myECMAPI.cancel_active_supplicants_to_start() #Makes sure any supplicant that might have conserved a "IN_PROGRESS"
    #status in the DB, because system crashed, or connection was lost, is set to CANCELED to waranty a fresh beginnning

    #obj2=DecisionMakerEngine()  #NOT possible as DecisionMakerEngine is singleton   
    #obj3= DecisionMakerEngine.getInstance() #Use this method instead to call the same instance with a new name

    #this thread will be constantly making a decision based on the latest available _issues_data.
    #once a decision is taken, it opens a supplicant. Each iteration, it asks the REST server for issues_data
    # NOTE: It modifies the value of supplicant_registry (TODO: mutex)
    # t = threading.Thread(target=obj.apply_decision_methodology, args=())
    # t.daemon= True
    # t.start()

    #this thread will be constantly listening any incomming response from ECM (EE2EL) and will notify DM parameters to  
    #decide whether it should continue or regret. 
    # NOTE: It modifies the value of supplicant_registry (TODO: mutex)
    # t2 = threading.Thread(target=obj.ECM_listener, args=())
    # t2.daemon= True
    # t2.start()

    #this thread runs the REST server of DM Component
    t3= threading.Thread(target=lambda: app.run(port=5000, debug=True, use_reloader=False))
    t3.daemon= True
    t3.start()

    while True:
        
        time.sleep(0.5)
