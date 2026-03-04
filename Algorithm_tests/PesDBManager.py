import time
from datetime import datetime
import sqlite3
from sqlite3 import Error
import os
import logging

dirname, filename = os.path.split(os.path.abspath(__file__))
log_path=str(dirname)
filename_log= log_path+"/LOGS/PESDMManager.log"

# create logger
loggerPESDB = logging.getLogger('PES-DB-MANAGER')
loggerPESDB.setLevel(logging.DEBUG)
# create console handler and set level to debug
chPESDB = logging.FileHandler(filename_log, mode='w')
chPESDB.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to chPESDB
chPESDB.setFormatter(formatter)
# add chPESDB to logger
loggerPESDB.addHandler(chPESDB)

class PESDBManager ():

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
            loggerPESDB.error("DATABASE MANAGEMENT: error creating DB-> "+ str(err))
            query=None

        return query



    #Name:create_pes_table
    #creates a a table with the given name.
    #Parameters: table_name[str]
    #return: None

    def create_pes_table(self, table_name="pes_registry"):
        query= """CREATE TABLE IF NOT EXISTS """ + str(table_name)+"""(
    task_id VARCHAR(40) NOT NULL PRIMARY KEY,
    pes VARCHAR(40),
    time_stamp DATETIME);"""  
    #SQLite sets AUTO_INCREMENT by default to its PRIMARY KEY        
        self.execute_query(query)



    #Name:drop_pes_table
    #deletes a a table (and all its data) with the given name.
    #Parameters: table_name[str]
    #return:None

    def drop_pes_table(self, table_name="pes_registry"):

        query = """DROP TABLE """ +str(table_name) +";"
        self.execute_query(query)



    #Name:clear_pes_table
    #deletes all data stored in certain table but not the table itself.
    #Parameters: table_name[str]
    #return:None

    def clear_pes_table(self, table_name="pes_registry"):

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
            print ("DATABASE REQUEST", db_name)
            connection = sqlite3.connect(database=db_name, check_same_thread=False)
        except Error as err:
            loggerPESDB.error ("DATABASE MANAGEMENT: error creating db connection-> "+ str(err))

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
            pes_id= cursor.lastrowid
    # connection.commit -->This method commits the current transaction. 
    # If you don't call this method, anything you did since the last call to commit() 
    # is not visible from other database connections.
        except Error as err:
            loggerPESDB.error("DATABASE MANAGEMENT: error executing query: "+ str(query) + "-> "+ str(err))
            pes_id=0
        return pes_id



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
            loggerPESDB.error("DATABASE MANAGEMENT: error reading query: "+ str(query) + "-> "+ str(err))



    #Name:close_connection
    #closes the connection to the DB
    #Parameters: query[str] --> in SQL format
    #return:None

    def close_connection(self):

        try:
            self._dbconnection_.close()
        except Error as err:
            loggerPESDB.error("DATABASE MANAGEMENT: error closing db-> "+ str(err))



    #Name:select_all
    #selects latests 100 pes registries in DB
    #Parameters: 
    #return:results [list of tuples]

    def select_all(self):

        query="""SELECT * FROM pes_registry LIMIT 100;"""
        results= self.read_query(query)     

        return results



    #Name:select_pes_by_task_id
    #selects all pes from a given task
    #Parameters: task_id [str]
    #return:results [list of tuples]

    def select_pes_by_task_id(self,task_id):

        query="""SELECT  * FROM pes_registry WHERE task_id= '""" + str(task_id)+ """';"""
        #print (query)
        results= self.read_query(query)     

        return results


    #Name:insert_pew_into_registry
    #inserts a new row in the pes-registry (DB) 
    #Parameters: tak_id[str],task_id[str], pes[str]
    #return:None

    def insert_pes_into_registry(self,task_id, pes):
        res=self.select_pes_by_task_id(task_id)
        pes_registry_id="None"
        if res:
            self.update_pes_status(task_id, pes)
        else:
            try:
                time_stamp=datetime.now()          
                query="""INSERT INTO pes_registry (task_id, pes, time_stamp)
                VALUES ('"""+ str(task_id) +"','"+ str(pes)+"','"+ str(time_stamp)+"');"           
                pes_registry_id=self.execute_query(query)
            except Error as err:
                loggerPESDB.error ("DATABASE MANAGEMENT: error inserting pes-> "+ str(err))
                loggerPESDB.error ("DATABASE MANAGEMENT: Task might already exist;trying to update...")

        return pes_registry_id



    #Name:delete_task_from_registry
    #in case of required, deletes a certain task from pes-registry (DB) using its task_id
    #Parameters: task_id[str]
    #return:None

    def delete_task_from_registry(self,task_id):

        query="""DELETE FROM pes_registry WHERE task_id= '""" + str(task_id)+ """';"""
        self.execute_query(query)     



    #Name:update_pes_status
    #updates the status value of certain pes in the pes-registry (DB)
    #Parameters: task_id[str], pes[str]
    #return:None

    def update_pes_status(self, task_id, pes):

                # time_stamp=datetime.now()          
                # query="""INSERT INTO pes_registry (task_id, pes, time_stamp)
                # VALUES ('"""+ str(task_id) +"','"+ str(pes)+"','"+ str(time_stamp)+"');" 

        time_stamp=datetime.now()
        query="""UPDATE pes_registry SET pes = '""" + str(pes) + "', time_stamp = '""" + str(time_stamp) + """' WHERE task_id= '""" + str(task_id)+ """';"""
        print(query)
        self.execute_query(query)






if __name__ == '__main__':

    dirname, filename = os.path.split(os.path.abspath(__file__))
    db_path=str(dirname)+ "\\pes_registry.db"
    print ("database path is: ", db_path)
    myPESmanager=PESDBManager(db_path)  
    #myPESmanager.drop_pes_table() 
    myPESmanager.create_pes_table()
    print ("\n***getting pes by task_id**")
    r2=myPESmanager.select_pes_by_task_id('t1')
    print ("\n***insert task pes**")    
    myPESmanager.insert_pes_into_registry("t1","pes_edge")
    myPESmanager.insert_pes_into_registry("t2","pes_local")


    print ("\n***getting pes by task_id**")
    r2=myPESmanager.select_pes_by_task_id('t1')
    print (r2)

    print ("\n***getting all pes***")
    results=myPESmanager.select_all()
    print(results)

    time.sleep(2)

    print ("\n***update pes based on task_id***")
    myPESmanager.update_pes_status("t1", "pes_local")

    print ("\n***getting all pes***")
    results=myPESmanager.select_all()
    print(results)

    myPESmanager.clear_pes_table()

    myPESmanager.close_connection()
    