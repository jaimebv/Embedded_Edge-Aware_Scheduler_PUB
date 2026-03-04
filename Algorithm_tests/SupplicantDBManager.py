import time
import sqlite3
from sqlite3 import Error
import os
import logging

dirname, filename = os.path.split(os.path.abspath(__file__))
log_path=str(dirname)
filename_log= log_path+"/LOGS/SupplicantDBManager.log"

# create logger
loggerSupDBManager = logging.getLogger('SUPPLICANT-DB-MANAGER')
loggerSupDBManager.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.FileHandler(filename_log, mode='w')
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
loggerSupDBManager.addHandler(ch)

class SupplicantDBManager ():

    #constructor: when we create an object, we establish the connection to the DB
    def __init__(self,db_name) -> None:

        #defines the connection to the database as an attribute of the object. 
        #this attribute is to be always used in order to execute any query, thus, it was
        #simpler to set the connection as an attribute, rather than sending it always
        #as a parameter to every method
        self._dbconnection_=self.create_db_connection(db_name)



    #Name:create_database_query
    #creates a db with the given name.
    #Parameters: namedb[str]
    #return: None

    def create_database_query(self, namedb):

        try:
            query= "CREATE DATABASE IF NOT EXISTS "+str(namedb)+";"
        except Error as err:
            loggerSupDBManager.error("DATABASE MANAGEMENT: error creating DB-> "+ str(err))
            query=None

        return query



    #Name:create_supplicants_table
    #creates a a table with the given name.
    #Parameters: table_name[str]
    #return: None

    def create_supplicants_table(self, table_name="supplicant_registry"):
        query= """CREATE TABLE IF NOT EXISTS """ + str(table_name)+"""(
    supplicant_id INTEGER PRIMARY KEY,
    task_id VARCHAR(40) NOT NULL,
    status VARCHAR(40),
    enim VARCHAR(40),
    time_stamp REAL,
    hold_time INTEGER,
    max_request INTEGER,
    request_performed INTEGER,
    RE2EL INTEGER);"""  
    #SQLite sets AUTO_INCREMENT by default to its PRIMARY KEY        
        self.execute_query(query)



    #Name:drop_supplicants_table
    #deletes a a table (and all its data) with the given name.
    #Parameters: table_name[str]
    #return:None

    def drop_supplicants_table(self, table_name="supplicant_registry"):

        query = """DROP TABLE """ +str(table_name) +";"
        self.execute_query(query)



    #Name:clear_supplicants_table
    #deletes all data stored in certain table but not the table itself.
    #Parameters: table_name[str]
    #return:None

    def clear_supplicants_table(self, table_name="supplicant_registry"):

        query = """DELETE FROM """ +str(table_name) +";"
        self.execute_query(query)



    #Name:create_db_connection
    #creates a connection with an sqlite database.
    #Parameters: db_name[str]
    #* db_name is the full path to the db
    #return:

    def create_db_connection(self,db_name):

        connection = None
        try:
            connection = sqlite3.connect(database=db_name, check_same_thread=False)
        except Error as err:
            loggerSupDBManager.error ("DATABASE MANAGEMENT: error creating db connection-> "+ str(err))
            

        return connection



    #Name:execute_query
    #generic method used to execute an SQL query.
    #Parameters: query[str] --> in SQL format
    #return:None

    def execute_query(self, query):

        cursor = self._dbconnection_.cursor()
        try:
            cursor.execute(query)
            self._dbconnection_.commit()
            supplicant_id= cursor.lastrowid
    # connection.commit -->This method commits the current transaction. 
    # If you don't call this method, anything you did since the last call to commit() 
    # is not visible from other database connections.
        except Error as err:
            loggerSupDBManager.error("DATABASE MANAGEMENT: error executing query: "+ str(query) + "-> "+ str(err))
            supplicant_id=0
        return supplicant_id



    #Name:read_query
    #generic method used to read information from DB using an SQL query.
    #Parameters: query[str] --> in SQL format
    #return:result [list]

    def read_query(self, query):

        cursor = self._dbconnection_.cursor()
        result = []
        try:
            cursor.execute(query)
            result = cursor.fetchall()

            return result

        except Error as err:
            loggerSupDBManager.error("DATABASE MANAGEMENT: error reading query: "+ str(query) + "-> "+ str(err))
           



    #Name:close_connection
    #closes the connection to the DB
    #Parameters: query[str] --> in SQL format
    #return:None

    def close_connection(self):

        try:
            self._dbconnection_.close()
        except Error as err:
            loggerSupDBManager.error("DATABASE MANAGEMENT: error closing db-> "+ str(err))
            



    #Name:select_all_supplicants
    #selects latests 100 supplicant registries in DB
    #Parameters: 
    #return:results [list of tuples]

    def select_all_supplicants(self):

        query="""SELECT * FROM supplicant_registry LIMIT 100;"""
        results= self.read_query(query)     

        return results



    #Name:select_supplicants_by_task_id
    #selects all supplicants that attend certain task defined by task_id from the supplicant_registry (DB)
    #Parameters: task_id [str], status[str]--> default=IN_PROGRESS
    #return:results [list of tuples]

    def select_supplicants_by_task_id(self,task_id, status="IN_PROGRESS"):

        query="""SELECT  * FROM supplicant_registry WHERE task_id= '""" + str(task_id)+ """' and status= '""" + str(status) + """';"""
        results= self.read_query(query)     

        return results



    #Name:select_supplicants_by_status
    #selects all supplicants that are currently in a certain status from the supplicant_registry (DB)
    #Parameters: status[str]--> default=IN_PROGRESS
    #return:results [list of tuples]

    def select_supplicants_by_status(self,status="IN_PROGRESS"):

        query="""SELECT  * FROM supplicant_registry WHERE status= '""" + str(status)+ """';"""
        results= self.read_query(query) 
        #loggerSupDBManager.debug ("DATABASE MANAGEMENT: db results-> "+ str(results))

        return results



    #Name:select_supplicants_by_id
    #selects a supplicants from the supplicant_registry (DB) by a given id
    #Parameters: supplicant_id[str]
    #return:results [list of tuples]

    def select_supplicants_by_supplicant_id(self, supplicant_id):

        query="""SELECT  * FROM supplicant_registry WHERE supplicant_id= '""" + str(supplicant_id)+ """';"""
        results= self.read_query(query) 
        #loggerSupDBManager.debug ("DATABASE MANAGEMENT: db results-> "+ str(results))

        return results




    #Name:get_latest_supplicant_id
    #returns the latest supplicant_id (row) registered in the table
    #Parameters: table_name[str]--> default="supplicant_registry"
    #return:results [int]

    def get_latest_supplicant_id(self,table_name="supplicant_registry" ):

        query="""SELECT supplicant_id FROM """ +str(table_name)+""" ORDER BY supplicant_id DESC LIMIT 1;"""
        res= self.read_query(query) 
        results=res[0][0]

        return results



    #Name:insert_supplicant_into_registry
    #inserts a new row in the supplicantsregistry (DB) 
    #Parameters: supplicant_id[str],task_id[str], enim[str], hold_time[int], max_requests[int], RE2EL[int]
    #return:None

    def insert_supplicant_into_registry(self,task_id, enim, hold_time, max_requests, RE2EL):

        try:
            time_stamp=time.time()           
            query="""INSERT INTO supplicant_registry (task_id, status, enim, time_stamp, hold_time, max_request, RE2EL)
            VALUES ('"""+ str(task_id) +"','IN_PROGRESS','" + str(enim) +"',"+ str(time_stamp) +","+ str(hold_time) +","+ str(max_requests) +"," + str(RE2EL)  +");"            
            supplicant_id=self.execute_query(query)
        except Error as err:
            loggerSupDBManager.error ("DATABASE MANAGEMENT: error inserting supplicant-> "+ str(err))
            supplicant_id=0

        return supplicant_id



    #Name:delete_supplicant
    #in case of required, deletes a certain supplicant from the supplicantsregistry (DB) using its supplicant_id
    #Parameters: supplicant_id[str]
    #return:None

    def delete_supplicant(self,supplicant_id):

        query="""DELETE FROM supplicant_registry WHERE supplicant_id= '""" + str(supplicant_id)+ """';"""
        self.execute_query(query)     



    #Name:update_supplicant_status
    #updates the status value of certain supplicant in the supplicantsregistry (DB)
    #Parameters: supplicant_id[str], status[str]
    #return:None

    def update_supplicant_status(self, supplicant_id, status):

        query="""UPDATE supplicant_registry SET status = '""" + str(status) + """' WHERE supplicant_id= '""" + str(supplicant_id)+ """';"""
        self.execute_query(query)



    #Name:set_supplicant_status_to_canceled
    #updates the status value of certain supplicant in the supplicantsregistry (DB) to CANCELED
    #Parameters: supplicant_id[str]
    #return:None

    def set_supplicant_status_to_canceled(self, supplicant_id):

        self.update_supplicant_status(supplicant_id, "CANCELED")



    #Name:set_supplicant_status_to_finished
    #updates the status value of certain supplicant in the supplicantsregistry (DB) to FINISHED
    #Parameters: supplicant_id[str]
    #return:None

    def set_supplicant_status_to_finished(self, supplicant_id):

        self.update_supplicant_status(supplicant_id, "FINISHED")



    #Name:set_supplicant_status_to_in_progress to IN_PROGRESS
    #updates the status value of certain supplicant in the supplicantsregistry (DB)
    #Parameters: supplicant_id[str]
    #return:None

    def set_supplicant_status_to_in_progress(self, supplicant_id):

        self.update_supplicant_status(supplicant_id, "IN_PROGRESS")



    #Name:set_supplicant_status_to_applied to COMPLETED
    #updates the status value of certain supplicant in the supplicantsregistry (DB)
    #Parameters: supplicant_id[str]
    #return:None

    def set_supplicant_status_to_completed(self, supplicant_id):

        self.update_supplicant_status(supplicant_id, "COMPLETED")
        



if __name__ == '__main__':

    dirname, filename = os.path.split(os.path.abspath(__file__))
    db_path=str(dirname)+ "\\supplicant_registry.db"
    print ("database path is: ", db_path)
    mysupplicantmanager=SupplicantDBManager(db_path)   
    mysupplicantmanager.create_supplicants_table()
    mysupplicantmanager.insert_supplicant_into_registry("t1","192.168.1.100",20,5,80)
    mysupplicantmanager.insert_supplicant_into_registry("t2","192.168.1.100",2,2,200)

    print ("\n***getting all supplicants for task 1 IN_PROGRESS***")
    r2=mysupplicantmanager.select_supplicants_by_task_id('t1')
    print (r2)

    print ("\n***setting supplicant (2) status to CANCEL***")
    mysupplicantmanager.set_supplicant_status_to_canceled('2')
    results=mysupplicantmanager.select_all_supplicants()
    print(results)

    print ("\n***setting supplicant (2) status to COMPLETED***")
    mysupplicantmanager.set_supplicant_status_to_completed('2')
    results=mysupplicantmanager.select_all_supplicants()
    print(results)

    print ("\n***inserting new supplicant***")
    mysupplicantmanager.insert_supplicant_into_registry("t5","192.168.1.100",20,20,180)
    mysupplicantmanager.insert_supplicant_into_registry("t6","192.168.1.100",60,60,88)
    results=mysupplicantmanager.select_all_supplicants()
    print(results)

    print ("\n***deleting latest supplicant***")
    mysupplicantmanager.delete_supplicant(mysupplicantmanager.get_latest_supplicant_id())
    results=mysupplicantmanager.select_all_supplicants()
    print(results)

    print("supp by id: ",mysupplicantmanager.select_supplicants_by_supplicant_id(1))

    mysupplicantmanager.clear_supplicants_table()
    mysupplicantmanager.close_connection()
    loggerSupDBManager.error ("DATABASE MANAGEMENT: testing logging")
    
