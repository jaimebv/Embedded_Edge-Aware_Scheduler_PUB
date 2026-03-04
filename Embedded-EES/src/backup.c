// /**
// * DESCRIPTION:
// * THE SOFTWARE IMPLEMENTS A REST API TO COMMUNICATE WITH THE REST OF THE EES AGENT.
// * BOTH SI AND TI COMPONENTS MUST RUN WITHIN THE EMBEDDED DEVICE 
// * THEREFORE, A REST API SERVER IS IMPLEMENTED TO RECEIVE INCOMMING REQUESTS
// *
// *
// * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED 
// * TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT 
// * SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN 
// * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE 
// * OR OTHER DEALINGS IN THE SOFTWARE. FURTHERMORE, THE SOFTWARE IS NOT MENT TO BE USED IN PRODUCTION AS IT ONLY 
// * SATISFIES ACADEMIC PURPOSES.
// *
// *
// *
// *
// * AUTHOR: JAIME BURBANO V
// * MODIFIED: 12/07/2022
// *
// *
// */


// #include <WiFi.h>
// #include <ESPAsyncWebServer.h>
// #include <SPIFFS.h>
// #include <ArduinoJson.h>
// #include "config.h"
// #include "ESP32_Utils_APIREST.h"
// #include <FreeRTOS.h>
// #include <HTTPClient.h>

// #define LOCAL_ADRESS "127.0.0.1"
// #define T1_LOCAL_PORT 8888
// #define LEN_QUEUE 3 //max 3 menssages in the queue
// #define LEN_MSG 60 //each message has 60 char

// AsyncWebServer server(80); //creates a server object

// String t1_pes=LOCAL_ADRESS;
// uint16_t t1_port=T1_LOCAL_PORT;
// uint16_t OE2EL_T1=0;
// uint16_t OE2EL_T2=0;
// uint16_t OE2EL_T3=0;



// xSemaphoreHandle xMutex;
// xSemaphoreHandle xMutexT1OE2EL; //mutex used to write and read OE2EL of T1 client
// xSemaphoreHandle xMutexT2OE2EL; //mutex used to write and read OE2EL of T2 client
// xSemaphoreHandle xMutexT3OE2EL; //mutex used to write and read OE2EL of T3 client

// TaskHandle_t xHandleTask1_server, xHandleTask1_client;
// TaskHandle_t xHandleTask2_server, xHandleTask2_client;
// TaskHandle_t xHandleTask3_server, xHandleTask3_client;



// xQueueHandle queue_message;
// String GetTaskStatus(uint8_t state); //function declaration



// /*
// * Returns task RTOS handler
// * @param task id as string
// * @return given task RTOS handler
// */
// TaskHandle_t getTaskHandler(String task_id){

//   if (task_id =="t1_client"){return xHandleTask1_client;}
//   if (task_id =="t1_server"){return xHandleTask1_server;}
//   if (task_id =="t2_client"){return xHandleTask2_client;}
//   if (task_id =="t2_server"){return xHandleTask2_server;}
//   if (task_id =="t3_client"){return xHandleTask3_client;}
//   else{return NULL;}

// }



// /*
// * Declares RTOS task 
// * @param pvParameters RTOS
// * @return void
// */
// void Task1_client(void *pvParameters)
// {

//   (void) pvParameters;
  
//   uint16_t port_connection= t1_port;
//   uint16_t value_t1, delay_time;
//   char *host=LOCAL_ADRESS;
//   uint32_t xStart, xEnd, xDifference;

//   while(true)
//   {
//     Serial.println("T1 Client*");
//     xStart = xTaskGetTickCount(); //returns the number of tick interrupts that have ocurred since the scheduler started

//     if( xMutex!= NULL ){

//       if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
//       {
//         host=const_cast<char*>(t1_pes.c_str());
//         port_connection=t1_port;
//         xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
//       }

//     }

//     else{
//       Serial.println("Error creating Mutex");  
//     }
//     //Serial.println("Attempting to connect to server ");
//     if(WiFi.status()== WL_CONNECTED){

//       WiFiClient client;
//       //Serial.println("Attempting to connect to: ");
//       //Serial.print(host);
//       //Serial.print(" :");
//       //Serial.print(port_connection);
//       client.connect( host, port_connection);
//       client.print("Hello from T1_client!");
//       client.stop(); //disconnect from server
//     }
//     /*
//     USED TO SIMULATE A PROCESSING DELAY WITH A POT
//     */
//     value_t1 = analogRead(34);  
//     delay_time=value_t1/2;
//     Serial.printf("\nt1_delay:%i\n",delay_time);   
//     vTaskDelay( delay_time / portTICK_PERIOD_MS ); //How many ticks the task is to be in BLOCKED state, so other
//                                                   //tasks can get to run
//     /*
//     ----------------------------------------------
//     */
//     xEnd = xTaskGetTickCount();
//     xDifference = xEnd - xStart;
//     //printf(" time: %" PRIu32 "\n",xDifference);

//     if( xMutexT1OE2EL!= NULL ){
      
//       if (xSemaphoreTake( xMutexT1OE2EL, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
//       {
//         OE2EL_T1=xDifference;


//         xSemaphoreGive(xMutexT1OE2EL); // MUST give back the mutex so other tasks can get it
//       }

//     }

//     else{
//       Serial.println("Error creating T1OE2ELMutex");  
//     }

//     vTaskDelay( 3000 / portTICK_PERIOD_MS );
//   } 
// }



// /*
// * Declares RTOS task 
// * @param pvParameters RTOS
// * @return void
// */
// void Task1_server(void *pvParameters)
// {

//   (void) pvParameters;
//   WiFiServer t1_server(t1_port);
//   t1_server.begin();

//   while(true){

//     WiFiClient client = t1_server.available();
    
//     if (client) {

//       if(client.connected())
//       {

//         Serial.println("\nClient Connected");
//       }
      
//       while(client.connected()){  

//         while(client.available()>0){
          
//           Serial.write(client.read()); // read data from the connected client
//         }
//       }

//       client.stop();
//       Serial.println("\nClient disconnected");    
//     }
//   }

//      vTaskDelay( 500 / portTICK_PERIOD_MS );
// }



// /*
// * Declares RTOS task 
// * @param pvParameters RTOS
// * @return void
// */
// void Task2_client(void *pvParameters)
// {
//   (void) pvParameters;
//   uint32_t xStart, xEnd, xDifference;

//   pinMode(13, OUTPUT);

//   while(true){

//     xStart = xTaskGetTickCount();

//     digitalWrite(13, HIGH);
//     vTaskDelay( 500 / portTICK_PERIOD_MS );
//     digitalWrite(13, LOW);    

//     xEnd = xTaskGetTickCount();  
//     xDifference = xEnd - xStart;
//     //printf(" time: %" PRIu32 "\n",xDifference);

//     if( xMutexT2OE2EL!= NULL ){

//       if (xSemaphoreTake( xMutexT2OE2EL, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
//       {

//         OE2EL_T2=xDifference;
//         xSemaphoreGive(xMutexT2OE2EL); // MUST give back the mutex so other tasks can get it
//       }
//     }

//     else {

//       Serial.println("Error creating T2OE2ELMutex");  
//     }

//     vTaskDelay( 500 / portTICK_PERIOD_MS );
//   }
// }



// /*
// * Declares RTOS task 
// * @param pvParameters RTOS
// * @return void
// */
// void Task3_client(void *pvParameters)
// {

//   (void) pvParameters;
//   uint32_t xStart, xEnd, xDifference;
//   uint16_t value=0;
//   uint16_t delay_time=200;
//   pinMode(25, OUTPUT);

//   while(true)
//   {

//     xStart = xTaskGetTickCount();

//     digitalWrite(25, HIGH);
//     value = analogRead(35);  
//     delay_time=value/2;
//     Serial.printf("\nt3_delay:%i\n",delay_time);  
//     vTaskDelay( delay_time / portTICK_PERIOD_MS );
//     digitalWrite(25, LOW);

//     xEnd = xTaskGetTickCount();
//     xDifference = xEnd - xStart;
//     //printf(" time: %" PRIu32 "\n",xDifference);

//     if( xMutexT3OE2EL!= NULL ){

//       if (xSemaphoreTake( xMutexT3OE2EL, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
//       {
//         OE2EL_T3=xDifference;
//         xSemaphoreGive(xMutexT3OE2EL); // MUST give back the mutex so other tasks can get it
//       }
//     }

//     else{
//       Serial.println("Error creating T3OE2ELMutex");  
//     }

//     vTaskDelay( 200 / portTICK_PERIOD_MS );
//   }
// }
  


// /*
// * Declares RTOS task 
// * @param pvParameters RTOS
// * @return void
// */
// void SI_notifier(void *pvParameters)
// {
//   (void) pvParameters;

//   uint16_t _OE2EL_T1=0, _OE2EL_T2=0, _OE2EL_T3=0;
  
//   while(true){

//     uint8_t task_state =255;
//     String task_state_str="";
//     String SI_message="";
    
//     Serial.print("sending POST from SI: ");
//     HTTPClient http;
//     http.begin(TASK_MONITOR_ISSUES_ENDPOINT);

//     //TODO: All task information could be stored in a struct element (sort of array)
//     //and then SI_notifier will iterate through all elements and get individual information 
//     //to form the message 
//     if( xMutexT1OE2EL!= NULL ){

//       if (xSemaphoreTake( xMutexT1OE2EL, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
//       {

//         _OE2EL_T1=OE2EL_T1;
//         //compare if latest write is 2x higher than individual average latency
//         // if yes, it is a timeout
//         xSemaphoreGive(xMutexT1OE2EL); // MUST give back the mutex so other tasks can get it
//       }
//     }

//     else{

//       Serial.println("Error creating T1OE2ELMutex");  
//     }

//     if( xMutexT2OE2EL!= NULL ){

//       if (xSemaphoreTake( xMutexT2OE2EL, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
//       {

//         _OE2EL_T2=OE2EL_T2;
//         xSemaphoreGive(xMutexT2OE2EL); // MUST give back the mutex so other tasks can get it
//       }
//     }
//     else{

//       Serial.println("Error creating T2OE2ELMutex");  
//     }

//     if( xMutexT3OE2EL!= NULL ){
//       if (xSemaphoreTake( xMutexT3OE2EL, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
//       {

//         _OE2EL_T3=OE2EL_T3;
//         xSemaphoreGive(xMutexT3OE2EL); // MUST give back the mutex so other tasks can get it
//       }
//     }

//     else{
//       Serial.println("Error creating T3OE2ELMutex");  
//     }
    
    
    
//     task_state=  eTaskGetState(xHandleTask1_client);
//     task_state_str=GetTaskStatus(task_state);
//     SI_message="{\"tasks\":{\"t1\":{\"id\":\"t1\",\"OE2EL\":"+ String(_OE2EL_T1)+ ",\"state\":\"" + task_state_str+ "\""+ ",\"priority\":\"" + String(uxTaskPriorityGet( xHandleTask1_client ))+ "\"},";
//     task_state=  eTaskGetState(xHandleTask2_client);
//     task_state_str=GetTaskStatus(task_state);
//     SI_message=SI_message + "\"t2\":{\"id\":\"t2\",\"OE2EL\":"+ String(_OE2EL_T2)+ ",\"state\":\"" + task_state_str+ "\""+ ",\"priority\":\"" + String(uxTaskPriorityGet( xHandleTask2_client ))+ "\"},";
//     task_state=  eTaskGetState(xHandleTask3_client);
//     task_state_str=GetTaskStatus(task_state);
//     SI_message=SI_message + "\"t3\":{\"id\":\"t3\",\"OE2EL\":"+ String(_OE2EL_T3)+ ",\"state\":\"" + task_state_str+ "\""+ ",\"priority\":\"" + String(uxTaskPriorityGet( xHandleTask3_client ))+ "\"}}}";
//     //Serial.println (SI_message);
//     //Add a 4 state which is TIMEOUT

//     if(WiFi.status()== WL_CONNECTED){

//       //HTTPClient http; //code always create a new http object into the loop
//       //http.begin(local_pes);
//       http.addHeader("Content-Type", "application/json");
//       int httpResponseCode = http.POST(SI_message);         

//       if(httpResponseCode>0){
        
//         //String response = http.getString(); //Get the response to the request
//         //Serial.println(httpResponseCode);   //Print return code
//         //Serial.println(response);           //Print request answer
        
//       }

//       else{
        
//         Serial.print("Error on sending POST from SI: ");
//         Serial.println(httpResponseCode);
        
//       }
//     }
    
//     vTaskDelay( 2000 / portTICK_PERIOD_MS );
//   }
// }




// /*
// * Declares RTOS task 
// * @param pvParameters RTOS
// * @return void
// */
// void TI_notifier(void *pvParameters)
// {
//   (void) pvParameters;
    
//   while(true){

//     char Rx[LEN_MSG];
//     //Serial.println("READING MESSAGE FROM QUEUE");
//     if(xQueueReceive(queue_message,&Rx,10000/portTICK_RATE_MS)==pdTRUE) {//10s --> max time that the task is blocked if the queue is empty
//       // for(uint8_t i=0; i<strlen(Rx); i++)
//       // {
//       //     Serial.printf("%c",Rx[i]);
//       // }
//       // if a message is in the queue, then notify the pes update to Task Monitor
//       if(WiFi.status()== WL_CONNECTED){
//         HTTPClient http;
//         http.begin(TASK_MONITOR_PES_ENDPOINT);
//         http.addHeader("Content-Type", "application/json");
//         int httpResponseCode = http.POST(String(Rx));         

//         if(httpResponseCode>0){
          
//           //String response = http.getString(); //Get the response to the request
//           //Serial.println(httpResponseCode);   //Print return code
//           //Serial.println(response);           //Print request answer
          
//         }

//         else{
          
//           Serial.print("Error on sending POST from TI notifier: ");
//           Serial.println(httpResponseCode);
          
//         }
//       }

//     } else{
//         Serial.println("Timeout when reading from queue");
//     }
   
//     vTaskDelay( 20 / portTICK_PERIOD_MS );
//   }
// }




// /*
// * Returns task scheduler state
// * @param task state 
// * @return String
// */
// String GetTaskStatus(uint8_t state){
//   String status_str="NULL";
//   switch(state)
//     {
//         case 0:
//             status_str="RUNNING";
//             break;

//         case 1:
//             status_str="READY";
//             break;

//         case 2:
//             status_str="BLOCKED";
//             break;

//         case 3:
//             status_str="SUSPENDED";
//             break;

//         case 4:
//             status_str="DELETED";
//             break;

//         default:
//             status_str="NULL";
//     }

//   return status_str;
// }





// /*
// * Returns all pes task information
// * @param *request pointer to the request
// * @return void
// * TODO: implement a mutex to hold resource
// */
// void getAll(AsyncWebServerRequest *request)
// {
//   String message = "Get All pes";
//   Serial.println(message);
//   request->send(200, "text/plain", message);
// }



// /*
// * Formats temperature and humidity gotten from sensor in a common format
// * @param sensor_type the type of sensor (currently only DH11 is supported)
// * @return void
// * TODO: implement a mutex to hold resource
// */
// void getById(AsyncWebServerRequest *request)
// {
//   String id = GetInfoFromURL(request, "/pes/");
//   String message = String("Get by Id ") + id;
//   Serial.println(message);
//   request->send(200, "text/plain", message);
// }



// /*
// * Formats temperature and humidity gotten from sensor in a common format
// * @param sensor_type the type of sensor (currently only DH11 is supported)
// * @return void
// * TODO: implement a mutex to hold resource
// */
// void getRequest(AsyncWebServerRequest *request) {
  
//   if(request->url().indexOf("/pes/") != -1)
//   {
//     getById(request);
//   }
//   else {
//     getAll(request);
//   }
// }



// /*
// * [Task Interface] Implements the function to respond an HTTP POST on /pes-update endpoint
// * @param *request, *data, data length, 
// * @return void
// */
// void postPesUpdate(AsyncWebServerRequest * request, uint8_t *data, size_t len, size_t index, size_t total)
// { 
//   HTTPClient http2;
//   http2.begin(TASK_MONITOR_PES_ENDPOINT);
//   String TI_message="{\"id\":\"t1\",\"new_pes\":\"pes-local\"}";
//   String current_pes;  
//   String bodyContent = GetBodyContent(data, len);
//   Serial.println(bodyContent);
//   StaticJsonDocument<200> doc;
//   DeserializationError error = deserializeJson(doc, bodyContent);
  
//   if (error) { request->send(400); return;}

//   String task_id = doc["task_id"];
//   String new_pes = doc["pes"];
//   String new_port = doc["port"];

//   String message = "update pes for " + task_id + " migrating to: "+ new_pes + " on port: " + new_port;
//   request->send(200, "text/plain", message);
//   //TODO also must suspend server task here in case it was not suspended already
//   // We could also need to resume the local task
//   // if we delete the task we save resources bu will need to reassign them once the task is to be created again
//   //TODO check if DM logic is able to ask to suspend a local task
//   //TODO send OE2EL
//   Serial.println(message);
//   if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
//   {
//       if (task_id=="t1"){
        
//         if (new_pes==LOCAL_ADRESS){
//           t1_pes=LOCAL_ADRESS;
//           t1_port=T1_LOCAL_PORT;
//           current_pes= "pes_local";
//         }
//         else{
//           t1_pes=new_pes;
//           t1_port=new_port.toInt();
//           current_pes= "pes_edge";
//         }
//       }
//       TI_message="{\"id\":\"" + task_id +"\",\"new_pes\":\""+ current_pes+"\"}";;
//       Serial.println (TI_message);
//       xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
//   }
//   //put message of pes update into a queue than will be read by TI_notifier task
//   //as if we try to do it here, and for some reason TM Component is not running properly, the embedded device
//   //will reboot constantly due to a POST request causing time out in the AsyncWebServer libary
//   char char_array[TI_message.length()+1];
//   TI_message.toCharArray(char_array, TI_message.length()+1);
//   Serial.println("putting message into QUEUE");
//   if (xQueueSendToBack(queue_message, &char_array,2000/portTICK_RATE_MS)!=pdTRUE){//2seg--> max time that the task is blocked if the queue is full
//       Serial.printf("error-> put pes update in queue\n");
//   }
//   Serial.println("queue put -> OK");
  
// }



// /*
// * [Task Interface] Implements the function to respond an HTTP POST on /resume-task endpoint
// * @param *request, *data, data length, 
// * @return void
// */
// void resumeTask(AsyncWebServerRequest * request, uint8_t *data, size_t len, size_t index, size_t total)
// { 
//   String bodyContent = GetBodyContent(data, len);

//   StaticJsonDocument<200> doc;
//   DeserializationError error = deserializeJson(doc, bodyContent);
//   if (error) { request->send(400); return;}

//   String task_id = doc["task_id"];
//   String type = doc["type"];
//   String task_to_resume = task_id +"_" + type;
//   String message = "resume: "+ task_to_resume;
//   Serial.println(task_to_resume); 
//   if (getTaskHandler(task_to_resume)!=NULL){
//     try{
//       vTaskResume(getTaskHandler(task_to_resume));
//       request->send(200, "text/plain", message);
//       throw (0);
//     }
//     catch (int error_code) {
//        request->send(304, "text/plain", "None");
//     }
//   }
//   else{
//     Serial.println("Task does not exist, thus cannot resume");
//     request->send(400, "text/plain", "None");
//   }
  
// }



// /*
// * [Scheduler Interface] Communicates the scheduler to suspend the task specified in 
// * the request after /task/ 
// * @param *request a pointer to the incomming request
// * @return void
// */
// void suspendTask(AsyncWebServerRequest *request) {

//   String id = GetInfoFromURL(request, "/suspend-task/");
//   String message = String("Suspends ") + id;
//   Serial.println(message);
//   if (getTaskHandler(id)!=NULL){
//     try{
//       vTaskSuspend(getTaskHandler(id));
//       request->send(200, "text/plain", message);
//       throw (0);
//     }
//     catch (int error_code) {
//        request->send(304, "text/plain", "None");
//     }
//   }
//   else{
//     Serial.println("Task does not exist, thus cannot suspend");
//     request->send(400, "text/plain", "None");
//   } 
// }



// /*
// * Gets the string after a give root endpoint
// * @param *request a pointer to the incomming request 
// * @param root  the endpoint after which the param will be gotten
// * @return The given string after root
// */
// String GetInfoFromURL(AsyncWebServerRequest *request, String root)
// {
//   String string_id = "";
//   string_id = request->url();
//   string_id.replace(root, "");
  
//   return string_id;
// }



// /*
// * Concatenates raw http post request data into a single string object
// * @param *data pointer to data, 
// * @param len data length
// * @return Data cointained into a String object
// */
// String GetBodyContent(uint8_t *data, size_t len)
// {
//   String content = "";
//   for (size_t i = 0; i < len; i++) {
//     content .concat((char)data[i]);
//   }
//   return content;
// }



// /*
// * Method to connect to WiFi in STA mode. It can use an static IP defined in config.h
// * @param useStaticIP false if network does not allow it
// * @return void
// */
// void ConnectWiFi_STA(bool useStaticIP)
// {
//    Serial.println("");
//    WiFi.mode(WIFI_STA);
//    WiFi.begin(ssid, password);
//    if(useStaticIP) WiFi.config(ip, gateway, subnet);
//    while (WiFi.status() != WL_CONNECTED) 
//    { 
//      delay(100);  
//      Serial.print('.'); 
//    }
 
//    Serial.println("");
//    Serial.print("Init STA:\t");
//    Serial.println(ssid);
//    Serial.print("IP address:\t");
//    Serial.println(WiFi.localIP());
// }



// /*
// * Method to connect to WiFi in AP mode. It can use an static IP defined in config.h
// * @param useStaticIP false if network does not allow it
// * @return void
// */
// void ConnectWiFi_AP(bool useStaticIP)
// { 
//    Serial.println("");
//    WiFi.mode(WIFI_AP);
//    while(!WiFi.softAP(ssid, password))
//    {
//      Serial.println(".");
//      delay(100);
//    }
//    if(useStaticIP) WiFi.softAPConfig(ip, gateway, subnet);

//    Serial.println("");
//    Serial.print("Iniciado AP:\t");
//    Serial.println(ssid);
//    Serial.print("IP address:\t");
//    Serial.println(WiFi.softAPIP());
// }



// /*
// * Implements the welcome message in case of a Home request
// * @param *request a pointer to the incomming request
// * @return void
// */
// void homeRequest(AsyncWebServerRequest *request) {
//   request->send(200, "text/plain", "Hello from EE-A");
// }



// /*
// * Implements a function in case the requested HTTP request is not found
// * @param *request a pointer to the incomming request
// * @return void
// */
// void notFound(AsyncWebServerRequest *request) {
// 	request->send(404, "text/plain", "Not found");
// }



// /*
// * Initialize REST API server
// * @return void
// */
// void InitServer()
// {
// 	server.on("/", HTTP_GET, homeRequest); //name_of_endpoint,HTTP_method,function_to_be_triggered
// 	server.on("/pes", HTTP_GET, getRequest);
// 	server.on("/pes-update", HTTP_POST, [](AsyncWebServerRequest * request){}, NULL, postPesUpdate);
// 	server.on("/resume-task", HTTP_POST, [](AsyncWebServerRequest * request){}, NULL, resumeTask);
// 	server.on("/suspend-task", HTTP_DELETE, suspendTask);
// 	server.onNotFound(notFound);

// 	server.begin(); // server starts listening to HTTP requests
//   Serial.println("HTTP server started");
// }



// void setup() 
// {
// 	Serial.begin(9600);
//   xMutex = xSemaphoreCreateMutex();
//   xMutexT1OE2EL = xSemaphoreCreateMutex();
//   xMutexT2OE2EL = xSemaphoreCreateMutex();
//   xMutexT3OE2EL = xSemaphoreCreateMutex();
//   queue_message= xQueueCreate(LEN_QUEUE, LEN_MSG);

// 	ConnectWiFi_STA(false);

// 	InitServer(); 

//   xTaskCreate(
//     &Task1_client
//     ,  "Task1_client"    
//     ,  4096      
//     ,  NULL
//     ,  2          
//     ,  &xHandleTask1_client);

//   xTaskCreate(
//     &Task1_server
//     ,  "Task1_server"    
//     ,  2048       
//     ,  NULL
//     ,  2          
//     ,  &xHandleTask1_server);

//   xTaskCreate(
//     &Task2_client
//     ,  "Task2_client"    
//     ,  2048       
//     ,  NULL
//     ,  1          
//     ,  &xHandleTask2_client);


//   xTaskCreate(
//     &Task3_client
//     ,  "Task3_client"    
//     ,  2048       
//     ,  NULL
//     ,  1          
//     ,  &xHandleTask3_client);


//   xTaskCreate(
//     &SI_notifier
//     ,  "SI_notifier"    
//     ,  4096       
//     ,  NULL
//     ,  2          
//     ,  NULL);

//   xTaskCreate(
//     &TI_notifier
//     ,  "TI_notifier"    
//     ,  4096       
//     ,  NULL
//     ,  2          
//     ,  NULL);


// }


// void loop() 
// {
// }