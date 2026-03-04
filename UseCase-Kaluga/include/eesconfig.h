#include <Arduino.h>
#include "SPIFFS.h"
#include "ArduinoJson.h"

#define CONFIG_FILE_PATH "/EESConfig.json"


/*
* Parses the EESConfig.json file to get all 
* required parameters to initialize the system
* @param None
* @return void
*/
void ParseConfigJsonFile();

/*
* Returns all pes task information
* @param id String: the name of the task as defined in EESConfig.json
* @param parameter String: the name of the specific parameter to retrieve
* @return requested parameter as string
*/
String GetTaskConfigParameter (String id, String parameter);

/*
* Returns app_type of a given task as defined in EESConfig.json
* @param id String: the name of the task as defined in EESConfig.json
* @return app_type as string
*/
String GetTaskConfigAppType (String id);

/*
* Returns MAE2EL of a given task as defined in EESConfig.json
* @param id String: the name of the task as defined in EESConfig.json
* @return MAE2EL as integer
*/
int GetTaskConfigMAE2EL (String id);

/*
* Returns the amount of resource units required by a given task as defined in EESConfig.json
* @param id String: the name of the task as defined in EESConfig.json
* @return resource units as integer
*/
uint8_t GetTaskConfigResources(String id);

/*
* Returns default primary execution site (pes) of a given task as defined in EESConfig.json
* @param id String: the name of the task as defined in EESConfig.json
* @return pes IP as string
*/
String GetTaskConfigPES (String id);

/*
* Returns connection port of a given task as defined in EESConfig.json
* @param id String: the name of the task as defined in EESConfig.json
* @return port as integer
*/
int GetTaskConfigPort(String id);
