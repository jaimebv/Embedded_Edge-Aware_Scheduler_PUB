import argparse
import os
import json
import SchedulerInterface
import time
import requests

def read_scenario(file_name):
    dirname, filename = os.path.split(os.path.abspath(__file__))
    path=str(dirname)+ "\\Scenarios"
    
    scenario_file=os.path.join(path,file_name)

    
    # Opening JSON file
    f = open(scenario_file)
    # returns JSON object as a dictionary
    scenario_data = json.load(f)

    return scenario_data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--scenario", help="the name of the scenario to simulate",default="Scenario1.json")
    args = parser.parse_args()
    scenario_data= read_scenario (args.scenario)


    rtos_file= scenario_data["file_name"]
    ue_locations= scenario_data["UE_location"]

    headers = {'Content-type': 'application/json', 'Accept': '*/*'}
    try:
        response_gotten = requests.post("http://localhost:5001/ecm/simulator/clientlocation/"+str(ue_locations),headers=headers)
        response_json=response_gotten.json()
        response=False
    except Exception as e:
        print ("COMMUNICATION DM: Error reaching ECM->" + str(e))

    print ("simulation:  ue location: ", ue_locations )
    SchedulerInterface.simulate_scenario(rtos_file)





    time.sleep (1)


