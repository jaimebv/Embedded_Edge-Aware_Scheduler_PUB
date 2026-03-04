import os
import json
from datetime import datetime

class DataTransformer():


    def __init__(self,file_name, type="JSON") -> None:
        self.data_file_name=file_name
        self.times_file_name=self.getTimeFileName(self.data_file_name)
        #print("**********")
        print( self.times_file_name)
        self.dirname, self.filename = os.path.split(os.path.abspath(__file__))
        data_file= self.dirname[:self.dirname.find("Data")]+ "\\LOGS\\"  +self.data_file_name
        print(data_file)
        f = open(data_file)
        information=f.readlines()
        self.data_list=[]

        for item in information:
            try:
                item = str(item).replace("\'","\"")
            
                res = json.loads(item)
            except:
                print(item)
            self.data_list.append(res)
        #self.data_list=self.data_list[4:]
        self.repalce_times_in_data(self.data_list)


    def getTimeFileName(self,data_file_name):
        
        date_file=data_file_name[data_file_name.find("_"):]
        time_file_name="ScenarioTimes"+date_file
        return time_file_name




    def repalce_times_in_data(self, data_list):
        res=""
        self.final_data_list=[]
        self.dirname, self.filename = os.path.split(os.path.abspath(__file__))
        self.times_file_name= self.dirname[:self.dirname.find("Data")]+ "\\LOGS\\"  +self.times_file_name
        print(self.times_file_name)



        f = open(self.times_file_name)
        information=f.readlines()


        for item in information:
            try:
                item=item.replace("\'","\"")
                res = json.loads(item)
                init_time=res["start"]
                init_time = datetime.strptime(init_time, '%Y-%m-%d %H:%M:%S.%f')
                print("******START TIME*******",init_time)
                end_time=res["end"]
                end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S.%f')
                print("*******END TIME*******",end_time)
                


                for data_frame in data_list:
                    date_time = datetime.strptime(data_frame["time"], '%Y-%m-%d %H:%M:%S,%f')
                    if date_time< init_time:
                        print("delete item BEFORE START")
                        print(data_frame)
                    elif date_time> end_time:
                        print("delete item AFTER END")
                        print(data_frame)
                    else:
                        data_frame["time"]=datetime.strftime(date_time, '%Y-%m-%d %H:%M:%S,%f')
                        self.final_data_list.append(data_frame)
                        
                    

                init_time=datetime.strftime(init_time, '%Y-%m-%d %H:%M:%S,%f')
                end_time=datetime.strftime(end_time, '%Y-%m-%d %H:%M:%S,%f')
                self.final_data_list[0]["time"]=init_time
                self.final_data_list[len(self.final_data_list)-1]["time"]=end_time
                #print(self.final_data_list)

            except Exception as e:
                print("ERROR:", item)
                print(e)




    def convertToCSV(self):
        import csv
 
        row_task_info_list=[]
        header = ['time']

        for key in self.final_data_list[10]["data"]["task_info"]:

            for key_internal in self.final_data_list[10]["data"]["task_info"][key]:
                header.append(key+"_"+key_internal)

        #print(header)

        for data in self.final_data_list:
            ind_task_info_list=[]
            ind_task_info_list.append(data["time"])

            for task_data in data["data"]["task_info"]:
                
                for individual_task_key in data["data"]["task_info"][task_data]:
                    c= data["data"]["task_info"][task_data][individual_task_key]
                    
                    if c == "BLOCKED" or c == "READY" or c == "RUNNING":
                        data["data"]["task_info"][task_data][individual_task_key]="ACTIVE"

                    ind_task_info_list.append(data["data"]["task_info"][task_data][individual_task_key])
                        

            row_task_info_list.append(ind_task_info_list)

        self.csv_file_name=self.dirname+"\\Files\\"+str(self.data_file_name)[:str(self.data_file_name).find(".")]+".csv"
        
        with open(self.csv_file_name, 'w', encoding='UTF8') as f:
            writer = csv.writer(f)
            writer.writerow(header)

            for row_data in row_task_info_list:
                writer.writerow(row_data)


    def convertToJSON(self):
        self.json_file_name=self.dirname+"\\Files\\"+str(self.data_file_name)[:str(self.data_file_name).find(".")]+".json"
        print(self.json_file_name)
        with open(self.json_file_name, 'w') as outfile:
            json.dump(self.final_data_list, outfile)


    def convertToBOTH(self):
        self.convertToJSON()
        self.convertToCSV()



if __name__ == '__main__':
    obj=DataTransformer("dataRaw_03-10-2022-10_43_19.log")
    #dataRaw_02-10-2022-12_39_55.log
    #obj.convertToJSON()
    #obj.convertToCSV()
    obj.convertToBOTH()
    