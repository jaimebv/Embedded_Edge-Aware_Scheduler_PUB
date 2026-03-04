# TESTING SYSTEM

**Latest-update_on:** 10-05-2022  
In order to test EES in this pull request, you need to use POSTMAN or any other similar Tool + several prompts running python with all dependencies installed.

## Steps:
1. Run Edge Diagnosis Platform un IntelliJ
2. Register one or more edge nodes using POSTMAN
   * Format as follows:
      * Request type: POST
      * URL: localhost:4567/rest/node/register
      * Headers: {'Content-type': 'application/json', 'Accept': '* / *'}
      * body: {
         "id" : "node1",
         "ipAddress": "68.131.232.11 : 30911",
         "connected" : true,
         "totalResource" : 2000000,
         "totalNetwork" : 2000000,
         "location" : 11,
         "heartBeatInterval" : 1500000
      }
3. Once request has been properly sent, you should see an incomming message in EDP consonsole
4. In individual anaconda prompts run: `TaskMonitor.py`, `DesicionMaker.py`, `ECM.py`
  
5. To simulate an scenario describen in scenario folder, you need to run `Scenariosimulator.py`. The script receives the scenario name as input argument using `-s`. By default it runs "Scenario1.json".

