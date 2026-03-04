#include "eesconfig.h"




DynamicJsonDocument configdoc(1024);



void ParseConfigJsonFile(){
  
  String config_file ="";
 
  if(!SPIFFS.begin(true)){
    Serial.println("An Error has occurred while mounting SPIFFS");
    return;
  }
  
  File file = SPIFFS.open(CONFIG_FILE_PATH);
  if(!file){
    Serial.println("Failed to open config file");
    return;
  }
  
  while(file.available()){
    config_file=config_file+(char)file.read();
  }
  file.close();
  deserializeJson(configdoc, config_file);
  
}

String GetTaskConfigParameter (String id, String parameter){

  String value = configdoc["tasks"][id][parameter];

  return value;

}

String GetTaskConfigAppType (String id){

  String value = configdoc["tasks"][id]["app_type"];

  return value;

}


int GetTaskConfigMAE2EL (String id){

  String value = configdoc["tasks"][id]["MAE2EL"];

  return value.toInt();

}


uint8_t GetTaskConfigResources(String id){

  String value = configdoc["tasks"][id]["resources"];

  return value.toInt();

}


String GetTaskConfigPES (String id){

  String value = configdoc["tasks"][id]["pes"];

  return value;

}



int GetTaskConfigPort(String id){

  String value = configdoc["tasks"][id]["port"];

  return value.toInt();

}

