/**
 * @file main.cpp
 * @brief REST API Server Implementation
 * 
 * DESCRIPTION:
 * THE SOFTWARE IMPLEMENTS A REST API TO COMMUNICATE WITH THE REST OF THE EES AGENT.
 * BOTH SI AND TI COMPONENTS MUST RUN WITHIN THE EMBEDDED DEVICE 
 * THEREFORE, A REST API SERVER IS IMPLEMENTED TO RECEIVE INCOMMING REQUESTS
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED 
 * TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT 
 * SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN 
 * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE 
 * OR OTHER DEALINGS IN THE SOFTWARE. FURTHERMORE, THE SOFTWARE IS NOT MENT TO BE USED IN PRODUCTION AS IT ONLY 
 * SATISFIES ACADEMIC PURPOSES.
 *
 * @author JAIME BURBANO V
 * @date 19/07/2022
 */



#include <ESPAsyncWebServer.h>
#include "networkconfig.h"
#include "eesconfig.h"
#include "ESP32_Utils_APIREST.h"
#include <freertos/FreeRTOS.h>
#include <HTTPClient.h>



#define LEN_QUEUE 3 //max 3 menssages in the queue
#define LEN_MSG 60 //each message has 60 char
#define TIMEOUT_THRESHOLD_MS 3000 //Defines the threshold after which a task is considered to enter in a timeout state
#define TOTAL_TASKS 4
//TASK MODIFY: Change this number to the number of tasks defined in the system 

AsyncWebServer server(80); //creates a server object

//Define task structure
typedef struct  {
  String   id;
  String   app_type;
  uint16_t MAE2EL;
  uint16_t last_start;
  uint16_t last_end;
  uint16_t OE2EL;
  String   state;
  String   pes;
  uint16_t port;
  uint8_t resources;
  boolean active;
} task;

task task_register[TOTAL_TASKS];
xSemaphoreHandle xMutex;

TaskHandle_t xHandleTask1_server, xHandleTask1_client;
TaskHandle_t xHandleTask2_server, xHandleTask2_client;
TaskHandle_t xHandleTask3_server, xHandleTask3_client;
//TASK MODIFY: Add here handlers for new tasks

xQueueHandle queue_message;//declare queue to transfer data from REST API to TI component 

String GetTaskStatus(uint8_t state); //function declaration



/**
 * Once the EESConfig.json has been read, the register of tasks must be filled
 * call this function before initializing the system
 * @param void
 * @return void
 */
void fillTaskRegister() {

  for(uint8_t i=1;i<TOTAL_TASKS;i++) {

    String id="t"+String(i);
    String _task_id_="t"+String(i)+"_client";
    //Serial.println(id);
    task_register[i].id=_task_id_;
    task_register[i].app_type=GetTaskConfigParameter(id,"app_type");
    task_register[i].MAE2EL=GetTaskConfigMAE2EL(id);
    task_register[i].last_start=0;
    task_register[i].last_end=0;
    task_register[i].OE2EL=0;
    task_register[i].state="RUNNING";
    task_register[i].pes=GetTaskConfigParameter(id,"pes");
    task_register[i].port=GetTaskConfigParameter(id,"port").toInt();
    task_register[i].resources=GetTaskConfigParameter(id,"resources").toInt();
    task_register[i].active=true;
    
  } 
}



/**
 * Prints out all tasks as defined in EESConfig.json
 * @param void
 * @return void
 */
void printTaskRegister(){
  for(uint8_t i=1;i<TOTAL_TASKS;i++) {
    Serial.print(task_register[i].id);
    Serial.print("\t");
    Serial.print(task_register[i].app_type);
    Serial.print("\t");
    Serial.print(task_register[i].pes);
    Serial.print("\t");
    Serial.print(task_register[i].port);
    Serial.print("\t");
    Serial.print(task_register[i].resources);
    Serial.println(task_register[i].active);
    
  }

}


/**
 * Prints out all tasks as defined in EESConfig.json
 * @param task_pos Position of the task in the register
 * @return void
 */
void printInfoTaskfromRegister(uint8_t task_pos){
    Serial.print(task_register[task_pos].id);
    Serial.print("\t");
    Serial.print(task_register[task_pos].app_type);
    Serial.print("\t");
    Serial.print(task_register[task_pos].pes);
    Serial.print("\t");
    Serial.print(task_register[task_pos].port);
    Serial.print("\t");
    Serial.print(task_register[task_pos].OE2EL);
    Serial.print("\t");
    Serial.println(task_register[task_pos].active);

}


/**
 * Returns task RTOS handler
 * @param task_id task id as string
 * @return given task RTOS handler
 */
TaskHandle_t getTaskHandler(String task_id){

  if (task_id =="t1_client"){return xHandleTask1_client;}
  if (task_id =="t1_server"){return xHandleTask1_server;}
  if (task_id =="t2_client"){return xHandleTask2_client;}
  if (task_id =="t2_server"){return xHandleTask2_server;}
  if (task_id =="t3_client"){return xHandleTask3_client;}
  else{return NULL;}
  //TASK MODIFY: Add here handlers for new tasks

}

/**
 * Returns task position in TaskRegister
 * @param task_id task id as string
 * @return position
 */
uint8_t getTaskPosinRegister(String task_id){

  if (task_id =="t1_client"){return 1;}
  if (task_id =="t2_client"){return 2;}
  if (task_id =="t3_client"){return 3;}
  else{return 0;}
  //TASK MODIFY: Add here handlers for new tasks

}

//**********************************       TASK DECLARAION        *************************************************
//*****************************************************************************************************************
/**
 * Declares RTOS task for Task 1 client
 * @param pvParameters RTOS
 * @return void
 */
void Task1_client(void *pvParameters)
{

  (void) pvParameters;
  
  uint16_t port_connection= GetTaskConfigParameter("t1","port").toInt(); //server port initial value
  uint16_t value_t1, delay_time, MAE2EL_T1;
  const char *host= LOCAL_ADRESS;//GetTaskConfigParameter("t1","pes"); //server IP initial value
  uint32_t xStart, xEnd, xDifference;
  boolean t1_active_flag=true;
  while(true)
  {
    xStart = xTaskGetTickCount(); //returns the number of tick interrupts that have ocurred since the scheduler started
    if( xMutex!= NULL ){
      if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
      {
        t1_active_flag=task_register[1].active;
        xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
      }
    }
    if (t1_active_flag){

      Serial.println("*T1 Client INIT*");

      if( xMutex!= NULL ){

        if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
        {

          task_register[1].last_start=xStart; //assign latest start tasks value
          host=const_cast<char*>(task_register[1].pes.c_str()); //assign latest registered server to local var
          port_connection=task_register[1].port; //assign latest registered port to local var
          xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
          MAE2EL_T1=task_register[1].MAE2EL;
        }

      }

      else{
        Serial.println("Error creating Mutex");  
      }

      //Attempting to connect to server
      if(WiFi.status()== WL_CONNECTED){

        WiFiClient client; //create a new WiFi client
        

        Serial.print("Attempting to connect to: ");
        Serial.print(host);
        Serial.print(" :");
        Serial.println(port_connection);
        
        //client.connect( host, port_connection);
        client.connect( host, port_connection,MAE2EL_T1*2); //latest param is te connection Timeout
        client.print("Hello from T1_client!");
        
        client.stop(); //disconnect from server
      }
      /*
      USED TO SIMULATE A PROCESSING DELAY WITH A POT
      */
      value_t1 = analogRead(34);  
      delay_time=value_t1;
      //Serial.printf("\nt1_delay:%i\n",delay_time);   
      vTaskDelay( delay_time / portTICK_PERIOD_MS ); //How many ticks the task is to be in BLOCKED state, so other
                                                    //tasks can get to run
      /*
      ----------------------------------------------
      */
      xEnd = xTaskGetTickCount();
      xDifference = xEnd - xStart;

      if( xMutex!= NULL ){
        
        if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
        {

          task_register[1].last_start=xStart; //assign latest start tasks value for Task1
          task_register[1].last_end=xEnd; //assign latest end tasks value
          task_register[1].OE2EL=xDifference; //assign latest measured OE2EL value
          Serial.print("***********OE2OE T1************");
          Serial.println(task_register[1].OE2EL);
          xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
        }

      }

      else{
        Serial.println("Error creating T1OE2ELMutex");  
      }

      
      Serial.print("*T1 Client END on:");
      Serial.print(host);
      Serial.print(" :");
      Serial.println(port_connection);
    } 
    else
    {
      //In case the active_flag is FALSE, then it is safe to suspend the task
      Serial.println("TASK: Suspend Task1");
      if( xMutex!= NULL ){
        if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
        {
          task_register[1].OE2EL=0;
          task_register[1].last_end=0; //assign latest end tasks value
          task_register[1].last_start=0; //assign latest start tasks value for Task1
          xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
        }
      }
      vTaskSuspend(NULL);
    }
    vTaskDelay( 200 / portTICK_PERIOD_MS );
    
  }
}



/*
* Declares RTOS task 
* @param pvParameters RTOS
* @return void
*/
void Task1_server(void *pvParameters)
{

  (void) pvParameters;
  WiFiServer t1_server(GetTaskConfigParameter("t1","port").toInt()); //creates a server that runs locally to attend enhanced task
  t1_server.begin(); //starts the server

  while(true){

    WiFiClient client = t1_server.available(); //creates an object of the server
    
    if (client) { //case it was possible to create the client
      Serial.println("\nWAITING CLIENT......\n");

      if(client.connected()) //case it was possible to establish the connection
      {
        Serial.println("\nClient Connected");
      } 

      while(client.connected()){  
        while(client.available()>0){      
          Serial.write(client.read()); // read data from the connected client
        }
      }

      client.stop(); //stop client
      Serial.println("\nClient disconnected");    
    }
    vTaskDelay( 10 / portTICK_PERIOD_MS );
  }

     
}



/*
* Declares RTOS task 
* @param pvParameters RTOS
* @return void
*/
void Task2_client(void *pvParameters)
{
  (void) pvParameters;
  uint32_t xStart, xEnd, xDifference;
  boolean t2_active_flag=true;

  pinMode(13, OUTPUT);

  while(true)
  {
    xStart = xTaskGetTickCount(); //returns the number of tick interrupts that have ocurred since the scheduler started
    if( xMutex!= NULL ){
      if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
      {
        t2_active_flag=task_register[2].active;
        xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
      }
    }
    if (t2_active_flag){


      digitalWrite(13, HIGH);
      vTaskDelay( 50 / portTICK_PERIOD_MS );
      digitalWrite(13, LOW);    

      xEnd = xTaskGetTickCount();  
      xDifference = xEnd - xStart;

      if( xMutex!= NULL ){

        if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
        {

          task_register[2].last_start=xStart; //assign latest start tasks value for Task2
          task_register[2].last_end=xEnd; //assign latest end tasks value for Task2
          task_register[2].OE2EL=xDifference; //assign latest measured OE2EL value for Task2

          xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
        }
      }

      else {

        Serial.println("Error creating xMutex");  
      }

      
    }
    else
    {
      //In case the active_flag is FALSE, then it is safe to suspend the task
      Serial.println("TASK: Suspend Task2");
      if( xMutex!= NULL ){
        if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
        {
          task_register[2].OE2EL=0;
          task_register[2].last_end=0; //assign latest end tasks value
          task_register[2].last_start=0; //assign latest start tasks value for Task2
          xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
        }
      }
      vTaskSuspend(NULL);
    }

    vTaskDelay( 100 / portTICK_PERIOD_MS );

  }
}



/*
* Declares RTOS task 
* @param pvParameters RTOS
* @return void
*/
void Task3_client(void *pvParameters)
{

  (void) pvParameters;
  uint32_t xStart, xEnd, xDifference;
  uint16_t value=0;
  uint16_t delay_time=200;
  boolean t3_active_flag=true;

  pinMode(25, OUTPUT);


  while(true)
  {
    xStart = xTaskGetTickCount(); //returns the number of tick interrupts that have ocurred since the scheduler started
    if( xMutex!= NULL ){
      if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
      {
        t3_active_flag=task_register[3].active;
        xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
      }
    }
    if (t3_active_flag){

      digitalWrite(25, HIGH);
      value = analogRead(35);  
      delay_time=value/2;
      //Serial.printf("\nt3_delay:%i\n",delay_time);  
      vTaskDelay( delay_time / portTICK_PERIOD_MS );
      digitalWrite(25, LOW);

      xEnd = xTaskGetTickCount();
      xDifference = xEnd - xStart;

      if( xMutex!= NULL ){

        if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
        {

          task_register[3].last_start=xStart; //assign latest start tasks value for Task3
          task_register[3].last_end=xEnd; //assign latest end tasks value for Task3
          task_register[3].OE2EL=xDifference; //assign latest measured OE2EL value for Task3
          xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
        }
      }

      else{
        Serial.println("Error creating T3OE2ELMutex");  
      }
    }

    else
    {
      //In case the active_flag is FALSE, then it is safe to suspend the task
      Serial.println("TASK: Suspend Task3");
      if( xMutex!= NULL ){
        if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
        {
          task_register[3].OE2EL=0;
          task_register[3].last_end=0; //assign latest end tasks value
          task_register[3].last_start=0; //assign latest start tasks value for Task3
          xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
        }
      }
      vTaskSuspend(NULL);
    }

    vTaskDelay( 100 / portTICK_PERIOD_MS );
  }
}
//TASK MODIFY: Add here any other tasks (clients or servers)

//********************************       END TASK DECLARATION       ***********************************************
//*****************************************************************************************************************



//********************************       EES TASK DECLARATION       ***********************************************
//*****************************************************************************************************************
/*
* Declares RTOS task 
* @param pvParameters RTOS
* @return void
*/
void SI_notifier(void *pvParameters)
{
  (void) pvParameters;

  uint16_t _OE2EL_T1=0, _OE2EL_T2=0, _OE2EL_T3=0;
  uint16_t _MAE2EL_T1=0, _MAE2EL_T2=0, _MAE2EL_T3=0;

  //TASK MODIFY: Add here more variables for new tasks
  
  while(true){

    uint8_t task_state =255;
    String task_state_str="";
    String SI_message="";
    
    // xStart1 = xTaskGetTickCount();

    //Serial.print("sending POST from SI: ");

    if( xMutex!= NULL ){

      if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
      {

        _OE2EL_T1=task_register[1].OE2EL;
        _MAE2EL_T1=task_register[1].MAE2EL;
        _OE2EL_T2=task_register[2].OE2EL;
        _MAE2EL_T2=task_register[2].MAE2EL;
        _OE2EL_T3=task_register[3].OE2EL;
        _MAE2EL_T3=task_register[3].MAE2EL;
        printInfoTaskfromRegister(1);

        xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
      }
    }

    else{

      Serial.println("Error creating T1OE2ELMutex");  
    }

    //TODO: Create the message in a loop

    task_state=  eTaskGetState(xHandleTask1_client);
    if (_OE2EL_T1>=_MAE2EL_T1*2 && task_state!=3){task_state=5;}

    task_state_str=GetTaskStatus(task_state);
    SI_message="{\"tasks\":{\"t1\":{\"id\":\"t1\",\"OE2EL\":"+ String(_OE2EL_T1)+ ",\"state\":\"" + task_state_str+ "\""+ ",\"priority\":\"" + String(uxTaskPriorityGet( xHandleTask1_client ))+ "\"},";
    
    task_state=  eTaskGetState(xHandleTask2_client);
    if (_OE2EL_T2>=_MAE2EL_T2*2 && task_state!=3){task_state=5;}
    task_state_str=GetTaskStatus(task_state);
    SI_message=SI_message + "\"t2\":{\"id\":\"t2\",\"OE2EL\":"+ String(_OE2EL_T2)+ ",\"state\":\"" + task_state_str+ "\""+ ",\"priority\":\"" + String(uxTaskPriorityGet( xHandleTask2_client ))+ "\"},";
    
    task_state=  eTaskGetState(xHandleTask3_client);
    if (_OE2EL_T3>=_MAE2EL_T3*2 && task_state!=3){task_state=5;}
    task_state_str=GetTaskStatus(task_state);
    SI_message=SI_message + "\"t3\":{\"id\":\"t3\",\"OE2EL\":"+ String(_OE2EL_T3)+ ",\"state\":\"" + task_state_str+ "\""+ ",\"priority\":\"" + String(uxTaskPriorityGet( xHandleTask3_client ))+ "\"}}}";

    //TASK MODIFY: Add here the info of the new tasks to thew SI_message
    if(WiFi.status()== WL_CONNECTED){
      HTTPClient http;
      http.begin(TASK_MONITOR_ISSUES_ENDPOINT);

      //http.begin(_TASK_MONITOR_ISSUES_ENDPOINT_,_TASK_MONITOR_ISSUES_ENDPOINT_PORT_,_TASK_MONITOR_ISSUES_ENDPOINT_PATH_);
      http.addHeader("Content-Type", "application/json");
      int httpResponseCode = http.POST(SI_message);         

      if(httpResponseCode<=0){
        
        Serial.print("Error on sending POST from SI: ");
        Serial.println(httpResponseCode);
        
      }
    }
    
    vTaskDelay( 100 / portTICK_PERIOD_MS );
  }
}




/*
* Declares RTOS task 
* @param pvParameters RTOS
* @return void
*/
void TI_notifier(void *pvParameters)
{
  (void) pvParameters;
    
  while(true){

    char Rx[LEN_MSG];
    //Serial.println("READING MESSAGE FROM QUEUE");
    if(xQueueReceive(queue_message,&Rx,1000/portTICK_RATE_MS)==pdTRUE) {//5s --> max time that the task is blocked if the queue is empty
      
      // for(uint8_t i=0; i<strlen(Rx); i++)
      // {
      //     Serial.printf("%c",Rx[i]);
      // }

      // if a message is in the queue, then notify the pes update to Task Monitor
      if(WiFi.status()== WL_CONNECTED){
        HTTPClient http;
        http.begin(TASK_MONITOR_PES_ENDPOINT);
        http.addHeader("Content-Type", "application/json");
        int httpResponseCode = http.POST(String(Rx));         

        if(httpResponseCode<=0){
          
          Serial.print("Error on sending POST from TI notifier to TaskMonitor: ");
          Serial.println(httpResponseCode);
          
        }
      }

    } else{
        Serial.println("Timeout when reading from queue");
    }
   
    vTaskDelay( 20 / portTICK_PERIOD_MS );
  }
}
//******************************       END EES TASK DECLARATION       *********************************************
//*****************************************************************************************************************



/**
 * Returns task scheduler state as string
 * @param state uint8_t representing task enum state
 * @return String task state
 */
String GetTaskStatus(uint8_t state){
  String status_str="NULL";
  switch(state)
    {
        case 0:
            status_str="RUNNING";
            break;

        case 1:
            status_str="READY";
            break;

        case 2:
            status_str="BLOCKED";
            break;

        case 3:
            status_str="SUSPENDED";
            break;

        case 4:
            status_str="DELETED";
            break;

        case 5:
            status_str="TIMEOUT";
            break;

        default:
            status_str="NULL";
    }

  return status_str;
}



/**
 * Returns all pes task information via REST
 * @param request pointer to the HTTP request
 * @return void
 */
void getAll(AsyncWebServerRequest *request)
{
  String message = "Get All pes";
  Serial.println(message);
  request->send(200, "text/plain", message);
}



/**
 * Returns information for a given task via REST
 * @param request pointer to the HTTP request
 * @return void
 */
void getById(AsyncWebServerRequest *request)
{
  String id = GetInfoFromURL(request, "/pes/");
  String message = String("Get by Id ") + id;
  Serial.println(message);
  request->send(200, "text/plain", message);
}



/**
 * Request handler resolving the GET endpoint
 * @param request pointer to the HTTP request
 * @return void
 */
void getRequest(AsyncWebServerRequest *request) {
  
  if(request->url().indexOf("/pes/") != -1)
  {
    getById(request);
  }
  else {
    getAll(request);
  }
}



/**
 * [Task Interface] Implements the function to respond to an HTTP POST on /pes-update endpoint
 * @param request pointer to the HTTP request
 * @param data pointer to the data payload
 * @param len data length
 * @param index data index
 * @param total data total length
 * @return void
 */
void postPesUpdate(AsyncWebServerRequest * request, uint8_t *data, size_t len, size_t index, size_t total)
{ 
  //HTTPClient http2;
  //http2.begin(TASK_MONITOR_PES_ENDPOINT);
  String TI_message="{\"id\":\"t1\",\"new_pes\":\"pes-local\"}";
  String current_pes;  
  String bodyContent = GetBodyContent(data, len);
  //Serial.println(bodyContent);
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, bodyContent);
  
  if (error) { request->send(400); return;}

  String task_id = doc["task_id"];
  String new_pes = doc["pes"];
  String new_port = doc["port"];

  String message = "update pes for " + task_id + " migrating to: "+ new_pes + " on port: " + new_port;
  request->send(200, "text/plain", message);
  //TODO: also must suspend server task here in case it was not suspended already
  // We could also need to resume the local task
  // if we delete the task we save resources but will need to reassign them once the task is to be created again
  //TODO: check if DM logic is able to ask to suspend a local task
  Serial.println(message);
  if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
  {
      if (task_id=="t1"){
        
        if (new_pes==LOCAL_ADRESS || new_pes==""){

          task_register[1].pes=LOCAL_ADRESS;
          task_register[1].port= GetTaskConfigParameter("t1","port").toInt();
          task_register[1].OE2EL=0;
          current_pes= "pes_local";
        }
        else{

          task_register[1].pes=new_pes;
          task_register[1].port=new_port.toInt();
          current_pes= "pes_edge";
        }
      }
      //TASK MODIFY: Add the same validation for all other enhanced or native tasks

      TI_message="{\"id\":\"" + task_id +"\",\"new_pes\":\""+ current_pes+"\"}";;
      Serial.println (TI_message);
      xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
  }
  //put message of pes update into a queue than will be read by TI_notifier task
  //as if we try to do it here, and for some reason TM Component is not running properly, the embedded device
  //will reboot constantly due to a POST request causing time out in the AsyncWebServer library
  char char_array[TI_message.length()+1];
  TI_message.toCharArray(char_array, TI_message.length()+1);
  //Serial.println("putting message into QUEUE");
  if (xQueueSendToBack(queue_message, &char_array,1000/portTICK_RATE_MS)!=pdTRUE){//1seg--> max time that the task is blocked if the queue is full
      //Serial.printf("error-> put pes update in queue\n");
  }
  else{
    //Serial.println("queue put -> OK");
  }
  
}



/*
* [Task Interface] Implements the function to respond an HTTP POST on /resume-task endpoint
* @param *request, *data, data length, 
* @return void
*/
void resumeTask(AsyncWebServerRequest * request, uint8_t *data, size_t len, size_t index, size_t total)
{ 
  String bodyContent = GetBodyContent(data, len);
  uint8_t task_pos_in_register=0;
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, bodyContent);
  if (error) { request->send(400); return;}

  String task_id = doc["task_id"];
  String type = doc["type"];
  String task_to_resume = task_id +"_" + type;
  String message = "resume: "+ task_to_resume;
  Serial.print("task_to_resume: "); 
  Serial.println(task_to_resume); 
  if (getTaskHandler(task_to_resume)!=NULL){
    try{

      if( xMutex!= NULL ){
        if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
        {
          task_register[getTaskPosinRegister(task_to_resume)].active=true;
          Serial.println("active_flag set to True");
          xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
        }
      }
      vTaskResume(getTaskHandler(task_to_resume));
      request->send(200, "text/plain", message);
      if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
      {

        task_pos_in_register=getTaskPosinRegister(task_to_resume);
        task_register[task_pos_in_register].OE2EL=0;
        task_register[task_pos_in_register].last_start=0;
        task_register[task_pos_in_register].last_end=0;

        xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
      }

      throw (0);
    }
    catch (int error_code) {
       request->send(304, "text/plain", "None");
    }
  }
  else{
    Serial.println("Task does not exist, thus cannot resume");
    request->send(400, "text/plain", "None");
  }
  
}



/*
* [Scheduler Interface] Communicates the scheduler to suspend the task specified in 
* the request after /task/ 
* @param *request a pointer to the incomming request
* @return void
*/
void suspendTask(AsyncWebServerRequest *request) {
  uint8_t task_pos_in_register=0;
  String id = GetInfoFromURL(request, "/suspend-task/");
  String message = String("Suspends ") + id;
  Serial.println(message);
  if (getTaskHandler(id)!=NULL){
    try{
      //vTaskSuspend(getTaskHandler(id));

      if( xMutex!= NULL ){
        if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
        {
          task_pos_in_register=getTaskPosinRegister(id);
          task_register[task_pos_in_register].active=false;
          Serial.println("active_flag set to False");
          //task_register[task_pos_in_register].last_start=0;
          //task_register[task_pos_in_register].last_end=0;
          xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
        }
      }

      request->send(200, "text/plain", message);
      throw (0);
    }
    catch (int error_code) {
       request->send(304, "text/plain", "None");
    }
  }
  else{
    Serial.println("Task does not exist, thus cannot suspend");
    request->send(400, "text/plain", "None");
  } 
}



/*
* Gets the string after a give root endpoint
* @param *request a pointer to the incomming request 
* @param root  the endpoint after which the param will be gotten
* @return The given string after root
*/
String GetInfoFromURL(AsyncWebServerRequest *request, String root)
{
  String string_id = "";
  string_id = request->url();
  string_id.replace(root, "");
  
  return string_id;
}



/*
* Concatenates raw http post request data into a single string object
* @param *data pointer to data, 
* @param len data length
* @return Data cointained into a String object
*/
String GetBodyContent(uint8_t *data, size_t len)
{
  String content = "";
  for (size_t i = 0; i < len; i++) {
    content .concat((char)data[i]);
  }
  return content;
}



/*
* Method to connect to WiFi in STA mode. It can use an static IP defined in config.h
* @param useStaticIP false if network does not allow it
* @return void
*/
void ConnectWiFi_STA(bool useStaticIP)
{
   Serial.println("");
   WiFi.mode(WIFI_STA);
   WiFi.begin(ssid, password);
   if(useStaticIP) WiFi.config(ip, gateway, subnet);
   while (WiFi.status() != WL_CONNECTED) 
   { 
     delay(100);  
     Serial.print('.'); 
   }
 
   Serial.println("");
   Serial.print("Init STA:\t");
   Serial.println(ssid);
   Serial.print("IP address:\t");
   Serial.println(WiFi.localIP());
}



/*
* Method to connect to WiFi in AP mode. It can use an static IP defined in config.h
* @param useStaticIP false if network does not allow it
* @return void
*/
void ConnectWiFi_AP(bool useStaticIP)
{ 
   Serial.println("");
   WiFi.mode(WIFI_AP);
   while(!WiFi.softAP(ssid, password))
   {
     Serial.println(".");
     delay(100);
   }
   if(useStaticIP) WiFi.softAPConfig(ip, gateway, subnet);

   Serial.println("");
   Serial.print("Iniciado AP:\t");
   Serial.println(ssid);
   Serial.print("IP address:\t");
   Serial.println(WiFi.softAPIP());
}



/*
* Implements the welcome message in case of a Home request
* @param *request a pointer to the incomming request
* @return void
*/
void homeRequest(AsyncWebServerRequest *request) {
  request->send(200, "text/plain", "Hello from EE-A");
}



/*
* Implements a function in case the requested HTTP request is not found
* @param *request a pointer to the incomming request
* @return void
*/
void notFound(AsyncWebServerRequest *request) {
	request->send(404, "text/plain", "Not found");
}



/*
* Initialize REST API server
* @return void
*/
void InitServer()
{
	server.on("/", HTTP_GET, homeRequest); //name_of_endpoint,HTTP_method,function_to_be_triggered
	server.on("/pes", HTTP_GET, getRequest);
	server.on("/pes-update", HTTP_POST, [](AsyncWebServerRequest * request){}, NULL, postPesUpdate);
	server.on("/resume-task", HTTP_POST, [](AsyncWebServerRequest * request){}, NULL, resumeTask);
	server.on("/suspend-task", HTTP_DELETE, suspendTask);
	server.onNotFound(notFound);

	server.begin(); // server starts listening to HTTP requests
  Serial.println("HTTP server started");
}



void setup() 
{
	Serial.begin(115200);
  while (!Serial){delay(2);}
  Serial.println("  ");
  xMutex = xSemaphoreCreateMutex();
  queue_message= xQueueCreate(LEN_QUEUE, LEN_MSG);

  ParseConfigJsonFile();
  fillTaskRegister();
  printTaskRegister();


	ConnectWiFi_STA(false);

	InitServer(); 

  xTaskCreate(
    &Task1_client
    ,  "t1_client"    
    ,  4096      
    ,  NULL
    ,  2          
    ,  &xHandleTask1_client);

  xTaskCreate(
    &Task1_server
    ,  "t1_server"    
    ,  2048       
    ,  NULL
    ,  2          
    ,  &xHandleTask1_server);

  xTaskCreate(
    &Task2_client
    ,  "t2_client"    
    ,  2048       
    ,  NULL
    ,  1          
    ,  &xHandleTask2_client);


  xTaskCreate(
    &Task3_client
    ,  "t3_client"    
    ,  2048       
    ,  NULL
    ,  1          
    ,  &xHandleTask3_client);


  xTaskCreate(
    &SI_notifier
    ,  "SI_notifier"    
    ,  4096       
    ,  NULL
    ,  2          
    ,  NULL);

  xTaskCreate(
    &TI_notifier
    ,  "TI_notifier"    
    ,  4096       
    ,  NULL
    ,  2          
    ,  NULL);


}


void loop() 
{
  vTaskDelay( 500 / portTICK_PERIOD_MS );
}