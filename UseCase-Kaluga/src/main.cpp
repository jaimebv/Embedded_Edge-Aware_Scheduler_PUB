/**
 *  @file main.cpp
 *  @brief Embedded Edge-Aware Scheduler (EEAS) Implementation
 *
 *  DESCRIPTION:
 *  THE SOFTWARE IMPLEMENTS THE EMBEDDED EDGE-AWARE SCHEDULER (EEAS) RUNNING TOGETHER WITH 3 TASKS
 *  IT USES A REST API TO COMMUNICATE WITH THE REST OF THE EEAS COMPONENTS.
 *  BOTH SI AND TI COMPONENTS RUN WITHIN THE EMBEDDED DEVICE AS TASKS
 *  THEREFORE, A REST API SERVER IS IMPLEMENTED TO RECEIVE INCOMMING REQUESTS
 *  THIS EXAMPLE IMPLEMENTS AN EDGE-ENHACED TASKS (TASK1) FOR FACE DETECTION
 *  when local execution, SW acquires images from the Kaluga V1.3 board and applies a simple embedded face 
 *  detecction algorithm. When remote execution is enabled, SW sends the captured frame via TCP
 *  to a Python Server. 
 *  Be aware, that in case you use any other ESP_CAM, or even other Kaluga board, 
 *  the pins must be redefined.
 *  IMPORTANT: this is only a test and cannot be used in production.
 *  BUGS:
 *  1) The system is not perfectly synch, thus it presents some issues when working faster than 100ms
 *  per loop.
 *  2) When the remote server is not available. The system reboots do to a problem im the WiFi Object creation in Task 1
 *  It is a known issue addressed here:  https://github.com/esp8266/Arduino/issues/230 
 *  TCP connection does close and free up memory but it takes some time. So frequent connection eat-up all the memory.
 *  Possible solution from the link above:
 *  in ClientContext.h
 *  64 err = tcp_close(_pcb);
 *  65 tcp_abort(_pcb); // Modification 28-06-2015
 *  66 if(err != ERR_OK) {
 *  67 DEBUGV(":tc err %d\r\n", err);
 *  68 tcp_abort(_pcb);
 *  69 err = ERR_ABRT;
 *  USE:
 *  1) Connect the camera to the Kaluga V1.3 board
 *  2) Make sure you have both USB cables connected (Power and Communication)
 *  3) Update the WiFi credential and the IP Address and port of the server
 *  4) [OPTIONAL] if you use any other board, you will need to update the camera pins
 *  5) Build the file systems and upload it (Build Filesystem Image (esp32-s2-kaluga-1)+ Upload Filesystem Image(esp32-s2-kaluga-1)) 
 *  from platform IO project tasks (first clik PIO icon in extenssions)
 *  5) Compile the code. If the esp_camera.h file is missing, add it from libraries in PlatformIO
 *  6) Make sure platformio.ini is as follows
 *  [env:esp32-s2-kaluga-1]
 *  platform = espressif32
 *  board = esp32-s2-kaluga-1
 *  framework = arduino
 *  monitor_speed = 115200
 *  lib_deps = 
 *   espressif/esp32-camera@^2.0.0
 *   ottowinter/ESPAsyncWebServer-esphome@^2.1.0
 *   bblanchon/ArduinoJson@^6.19.4
 *   FS
 *  board_build.partitions = huge_app.csv
 *  build_flags = 
 *   -DBOARD_HAS_PSRAM
 *   -mfix-esp32-psram-cache-issue
 *  monitor_filters = esp32_exception_decoder
 *  7) Deploy the code to the board
 *  8) Run the server in Python for face detection provided together with this file
 * 
 *  Copyright (C) 2023 IERSE Universidad del Azuay (Cuenca - Ecuador).
 *  http://www.uazuay.edu.ec
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU Lesser General Public License as published by
 *  the Free Software Foundation, either version 2.1 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Lesser General Public License for more details.
 *
 *  You should have received a copy of the GNU Lesser General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 *  @version 1.1
 *  @author Jaime Burbano
 */

//==========================================================================================================
#include <ESPAsyncWebServer.h>
#include "esp_camera.h"
#include "networkconfig.h"
#include "eesconfig.h"
#include "ESP32_Utils_APIREST.h"
#include <freertos/FreeRTOS.h>
#include <HTTPClient.h>

//  APPLICATION LIBRARIES
#include "img_converters.h"
#include "human_face_detect_msr01.hpp"
#include "human_face_detect_mnp01.hpp"





//**********************************       CAMERA DEFINITION        *************************************************
//*****************************************************************************************************************
#define CAM_PIN_PWDN 46  //power down is not used
#define CAM_PIN_RESET 45 //software reset will be performed
#define CAM_PIN_XCLK 1
#define CAM_PIN_SIOD 8
#define CAM_PIN_SIOC 7
#define CAM_PIN_D9 38
#define CAM_PIN_D8 21
#define CAM_PIN_D7 40
#define CAM_PIN_D6 39
#define CAM_PIN_D5 42
#define CAM_PIN_D4 41
#define CAM_PIN_D3 37
#define CAM_PIN_D2 36
#define CAM_PIN_VSYNC 2
#define CAM_PIN_HREF 3
#define CAM_PIN_PCLK 33
size_t length_pic;
static camera_config_t camera_config = {
  .pin_pwdn = CAM_PIN_PWDN,
  .pin_reset = CAM_PIN_RESET,
  .pin_xclk = CAM_PIN_XCLK,
  .pin_sscb_sda = CAM_PIN_SIOD,
  .pin_sscb_scl = CAM_PIN_SIOC,
  .pin_d7 = CAM_PIN_D9,
  .pin_d6 = CAM_PIN_D8,
  .pin_d5 = CAM_PIN_D7,
  .pin_d4 = CAM_PIN_D6,
  .pin_d3 = CAM_PIN_D5,
  .pin_d2 = CAM_PIN_D4,
  .pin_d1 = CAM_PIN_D3,
  .pin_d0 = CAM_PIN_D2,
  .pin_vsync = CAM_PIN_VSYNC,
  .pin_href = CAM_PIN_HREF,
  .pin_pclk = CAM_PIN_PCLK,
  //XCLK 20MHz or 10MHz for OV2640 double FPS (Experimental)
  .xclk_freq_hz = 20000000,
  .ledc_timer = LEDC_TIMER_0,
  .ledc_channel = LEDC_CHANNEL_0,
  .pixel_format = PIXFORMAT_JPEG,
  //.pixel_format = PIXFORMAT_JPEG, //YUV422,GRAYSCALE,RGB565,JPEG
  .frame_size = FRAMESIZE_QVGA,    //QQVGA-UXGA Do not use sizes above QVGA when not JPEG
  .jpeg_quality = 12, //0-63 lower number means higher quality
  .fb_count = 1,       //if more than one, i2s runs in continuous mode. Use only with JPEG
  .grab_mode = CAMERA_GRAB_WHEN_EMPTY,
};



//*****************************************************************************************************************

#define LEN_QUEUE 3 //max 3 menssages in the queue
#define LEN_MSG 60 //each message has 60 char
#define TIMEOUT_THRESHOLD_MS 3000 //Defines the threshold after which a task is considered to enter in a timeout state
#define TOTAL_TASKS 4
//TASK MODIFY: Change this number to the number of tasks defined in the system (always +1 that the client tasks)

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
 *  Once the EESConfig.json has been read, the register of tasks must be filled
 *  call this function before initializing the system
 *  @param void
 *  @return void
 */
void fillTaskRegister() {

  for (uint8_t i = 1; i < TOTAL_TASKS; i++) {

    String id = "t" + String(i);
    String _task_id_ = "t" + String(i) + "_client";
    //Serial.println(id);
    task_register[i].id = _task_id_;
    task_register[i].app_type = GetTaskConfigParameter(id, "app_type");
    task_register[i].MAE2EL = GetTaskConfigMAE2EL(id);
    task_register[i].last_start = 0;
    task_register[i].last_end = 0;
    task_register[i].OE2EL = 0;
    task_register[i].state = "RUNNING";
    task_register[i].pes = GetTaskConfigParameter(id, "pes");
    task_register[i].port = GetTaskConfigParameter(id, "port").toInt();
    task_register[i].resources = GetTaskConfigParameter(id, "resources").toInt();
    task_register[i].active = true;

  }
}



/**
 *  Prints out all tasks as defined in EESConfig.json
 *  @param void
 *  @return void
 */
void printTaskRegister() {
  for (uint8_t i = 1; i < TOTAL_TASKS; i++) {
    Serial.print(task_register[i].id);
    Serial.print("\t");
    Serial.print(task_register[i].app_type);
    Serial.print("\t");
    Serial.print(task_register[i].pes);
    Serial.print("\t");
    Serial.println(task_register[i].active);

  }
}


/**
 *  Prints out a tasks information as defined in EESConfig.json
 *  @param task_pos position of the task in the register
 *  @return void
 */
void printInfoTaskfromRegister(uint8_t task_pos) {
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
 *  Returns task RTOS handler
 *  @param task_id task id as string
 *  @return given task RTOS handler
 */
TaskHandle_t getTaskHandler(String task_id) {

  if (task_id == "t1_client") {
    return xHandleTask1_client;
  }
  if (task_id == "t1_server") {
    return xHandleTask1_server;
  }
  if (task_id == "t2_client") {
    return xHandleTask2_client;
  }
  if (task_id == "t2_server") {
    return xHandleTask2_server;
  }
  if (task_id == "t3_client") {
    return xHandleTask3_client;
  }
  else {
    return NULL;
  }
  //TASK MODIFY: Add here handlers for new tasks

}

/**
 *  Returns task position in TaskRegister
 *  @param task_id task id as string
 *  @return position
 */
uint8_t getTaskPosinRegister(String task_id) {

  if (task_id == "t1_client") {
    return 1;
  }
  if (task_id == "t2_client") {
    return 2;
  }
  if (task_id == "t3_client") {
    return 3;
  }
  else {
    return 0;
  }
  //TASK MODIFY: Add here handlers for new tasks

}


//**********************************       TASK FUNCTIONS        *************************************************
//*****************************************************************************************************************
uint8_t init_camera() {
  //initialize the camera
  Serial.println("Init Camera");
  uint8_t err = esp_camera_init(&camera_config);
  if (err != 0)
  { Serial.println("Camera Init Failed");
    return err;
  }
  return 0;
}

//**********************************       TASK DECLARAION        *************************************************
//*****************************************************************************************************************

/**
 * Declares RTOS task for client side of Task 1
 * @param pvParameters RTOS parameters
 * @return void
 */
void Task1_client(void *pvParameters)
{
  // -------------------------- SYSTEM VARIABLES DO NOT MODIFY -------------------------- 
  (void) pvParameters;
  #define TWO_STAGE 1 //to execute a more precise face detection algorithm

  uint16_t port_connection= GetTaskConfigParameter("t1","port").toInt(); //server port initial value
  uint16_t value_t1, delay_time, MAE2EL_T1;
  const char *host= "127.0.0.1";//GetTaskConfigParameter("t1","pes"); //server IP initial value
  //String new_pes=LOCAL_ADRESS;
  uint32_t xStart, xEnd, xDifference;
  boolean t1_active_flag=true;


  // //  -------------------------- START YOUR APPLICATION VARIABLES AND SET-UP -------------------------- 
  uint8_t error;
  error = init_camera(); //QQ
  // //TODO: Freeze if cammera cannot init

  while(true)
  {
    //  -------------------------- DECLARE APPLICATION CONSTANTS -------------------------- 
    size_t out_len, out_width, out_height;
    uint8_t *out_buf;
    bool s;
    bool buffer_malloc; 
    

    //  -------------------------- SYSTEM FUNCTIONS DO NOT MODIFY  -------------------------- 
    xStart = xTaskGetTickCount(); //returns the number of tick interrupts that have ocurred since the scheduler started
    if( xMutex!= NULL ){
      if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
      {
        t1_active_flag=task_register[1].active;
        host=const_cast<char*>(task_register[1].pes.c_str()); //assign latest registered server to local var
        //new_pes=task_register[1].pes;
        port_connection=task_register[1].port; //assign latest registered port to local var
        MAE2EL_T1=task_register[1].MAE2EL;
        xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
      }
    }
    if (t1_active_flag){ //case the task is marked as active and then can be normally executed

      Serial.println("*T1 Client INIT*");

      //  //-------------------------- START YOUR APLLICATION CODE HERE -------------------------- 
      camera_fb_t *fb = esp_camera_fb_get(); //get a frame from the camera
      if (!fb) {
        Serial.println("Camera capture failed");
        
      }
      else {
        if (strcmp(host, LOCAL_ADRESS) == 0){
          //  -------------------------- THIS IS DONE IN CASE OF LOCAL EXECUTION --------------------------        
          out_len = fb->width * fb->height * 3; //declares the number of bytes of the buffer to transform the image for face detection
          Serial.println("LOCAL EXECUTION");
          out_width = fb->width; //declares image width for face detection
          out_height = fb->height; //declares image height for face detection
          out_buf = (uint8_t *)malloc(out_len); //attempts to allocate an space of memory equals to the rgb image
          if (!out_buf) //case the memory cannot be allocated
          {
                Serial.print("[ERROR] out_buf malloc failed");
                esp_camera_fb_return(fb); //return the memory of the frame to dont waste our limited resources
          }
          else //case we were able to allocate the memory
          {
            s = fmt2rgb888(fb->buf, fb->len, fb->format, out_buf); //transform JPEG image into rgb888 for face detection and store the new image in out_buf
            esp_camera_fb_return(fb); //return the memory of the frame because now we only work with rgb888 image
            if (!s) //case something went wrong with the transformation
            {
              free(out_buf);
              Serial.print("[ERROR] To rgb888 failed");
            }
            else
            {

              #if TWO_STAGE
                HumanFaceDetectMSR01 s1(0.1F, 0.5F, 10, 0.2F);
                HumanFaceDetectMNP01 s2(0.5F, 0.3F, 5);
                std::list<dl::detect::result_t> &candidates = s1.infer((uint8_t *)out_buf, {(int)out_height, (int)out_width, 3});
                std::list<dl::detect::result_t> &results = s2.infer((uint8_t *)out_buf, {(int)out_height, (int)out_width, 3}, candidates);
              #else
                HumanFaceDetectMSR01 s1(0.3F, 0.5F, 10, 0.2F);
                std::list<dl::detect::result_t> &results = s1.infer((uint8_t *)out_buf, {(int)out_height, (int)out_width, 3});
              #endif
              free(out_buf); //liberate the memory allocated

              //Serial.println(results.size()); //results size > 0 if a face was detected
              
              if (results.size() > 0)
              {
                Serial.print("\n\n\n Face detected: ");
                Serial.println(results.size());
              }
            }
          }

        }
        else{
          //  -------------------------- THIS IS DONE IN CASE OF REMOTE EXECUTION --------------------------   

          // Use WiFiClient class to create TCP connections
          WiFiClient client;
          if (!client.connect(host, port_connection)) {
            Serial.println("connection failed");
            esp_camera_fb_return(fb);
            vTaskDelay( MAE2EL_T1*2 / portTICK_PERIOD_MS );
            
          }

          // This will send a string to the server
          //Serial.println("sending data to server");
          if (client.connected()) { 
            client.write((char *)fb->buf, fb->len);
            esp_camera_fb_return(fb);
            String req = client.readStringUntil('*'); //waits until the response from the server arrives
          }  
      }
    }




      //  -------------------------- SYSTEM FUNCTIONS DO NOT MODIFY  -------------------------- 
      xEnd = xTaskGetTickCount();
      xDifference = xEnd - xStart;

      if( xMutex!= NULL ){
        
        if (xSemaphoreTake( xMutex, portMAX_DELAY )==pdTRUE)//if i was able to get the mutex (no other task is ussing the resource)
        {

          task_register[1].last_start=xStart; //assign latest start tasks value for Task1
          task_register[1].last_end=xEnd; //assign latest end tasks value
          task_register[1].OE2EL=xDifference; //assign latest measured OE2EL value
          task_register[1].state="RUNNING"; //assign latest measured OE2EL value
          xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
          Serial.print("**OE2OE T1** ");
          Serial.println(xDifference);
        }

      }

      else{
        Serial.println("Error creating T1OE2ELMutex");  
      }
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
          task_register[1].state="SUSPENDED"; //assign latest measured OE2EL value
          xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
        }
      }
      vTaskSuspend(NULL);
    }
    vTaskDelay( 200 / portTICK_PERIOD_MS );
    
  }
}



/*
  Declares RTOS task
  @param pvParameters RTOS
  @return void
*/
void Task2_client(void *pvParameters)
{
  (void) pvParameters;
  uint32_t xStart, xEnd, xDifference;
  boolean t2_active_flag = true;
  uint16_t port_connection= GetTaskConfigParameter("t2","port").toInt(); //server port initial value
  uint16_t value_t2, delay_time, MAE2EL_T2;
  const char *host= "127.0.0.1";//;
  float randLat;
  float randLon;
  //pinMode(13, OUTPUT);

  while (true)
  {
    xStart = xTaskGetTickCount(); //returns the number of tick interrupts that have ocurred since the scheduler started
    if ( xMutex != NULL ) {
      if (xSemaphoreTake( xMutex, portMAX_DELAY ) == pdTRUE) //if i was able to get the mutex (no other task is ussing the resource)
      {
        t2_active_flag = task_register[2].active;
        host=const_cast<char*>(task_register[2].pes.c_str()); //assign latest registered server to local var
        port_connection=task_register[2].port; //assign latest registered port to local var
        MAE2EL_T2=task_register[2].MAE2EL;
        xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
      }
    }
    if (t2_active_flag) {

      Serial.println("*T2 Client INIT*");

      //  //-------------------------- START YOUR APLLICATION CODE HERE --------------------------
      Serial.print("connecting to ");
      Serial.print(host);
      Serial.print(':');
      Serial.println(port_connection);

      // Use WiFiClient class to create TCP connections
      WiFiClient client;
      if (!client.connect(host, port_connection)) {
        Serial.println("connection failed");
        vTaskDelay( MAE2EL_T2*2 / portTICK_PERIOD_MS );
        
      }
      if (client.connected()) { 
        randLat= (random(900)/1000.0)-2;
        randLon = (random(900)/1000.0)-75;
        delay(2); //emulate the data acquisition from GPS
        String gps="{\'Lat\':"+ String(randLat) + ",\'Lon\':"+ String(randLon)+"}" ;
        
        client.println(gps); 
        String req = client.readStringUntil('*');
        //Serial.println(req);
        }

      xEnd = xTaskGetTickCount();
      xDifference = xEnd - xStart;

      if ( xMutex != NULL ) {

        if (xSemaphoreTake( xMutex, portMAX_DELAY ) == pdTRUE) //if i was able to get the mutex (no other task is ussing the resource)
        {

          task_register[2].last_start = xStart; //assign latest start tasks value for Task2
          task_register[2].last_end = xEnd; //assign latest end tasks value for Task2
          task_register[2].OE2EL = xDifference; //assign latest measured OE2EL value for Task2
          task_register[2].state="RUNNING";
          xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
          Serial.print("**OE2OE T2** ");
          Serial.println(xDifference);
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
      if ( xMutex != NULL ) {
        if (xSemaphoreTake( xMutex, portMAX_DELAY ) == pdTRUE) //if i was able to get the mutex (no other task is ussing the resource)
        {
          task_register[2].OE2EL = 0;
          task_register[2].last_end = 0; //assign latest end tasks value
          task_register[2].last_start = 0; //assign latest start tasks value for Task2
          task_register[2].state="SUSPENDED";
          xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
        }
      }
      vTaskSuspend(NULL);
    }

    vTaskDelay( 2 / portTICK_PERIOD_MS );

  }
}



/*
  Declares RTOS task
  @param pvParameters RTOS
  @return void
*/
void Task3_client(void *pvParameters)
{

  (void) pvParameters;
  uint32_t xStart, xEnd, xDifference;
  uint16_t value = 0;
  uint16_t delay_time = 200;
  boolean t3_active_flag = true;
  uint8_t delay_ms_t;


  

  while (true)
  {
    xStart = xTaskGetTickCount(); //returns the number of tick interrupts that have ocurred since the scheduler started
    if ( xMutex != NULL ) {
      if (xSemaphoreTake( xMutex, portMAX_DELAY ) == pdTRUE) //if i was able to get the mutex (no other task is ussing the resource)
      {
        t3_active_flag = task_register[3].active;
        xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
      }
    }
    if (t3_active_flag) {

      delay_ms_t= random(5);
      vTaskDelay(delay_ms_t);

      xEnd = xTaskGetTickCount();
      xDifference = xEnd - xStart;

      if ( xMutex != NULL ) {

        if (xSemaphoreTake( xMutex, portMAX_DELAY ) == pdTRUE) //if i was able to get the mutex (no other task is ussing the resource)
        {

          task_register[3].last_start = xStart; //assign latest start tasks value for Task3
          task_register[3].last_end = xEnd; //assign latest end tasks value for Task3
          task_register[3].OE2EL = xDifference; //assign latest measured OE2EL value for Task3
          task_register[3].state="RUNNING";
          xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
          Serial.print("**OE2OE T3** ");
          Serial.println(xDifference);
        }
      }

      else {
        Serial.println("Error creating T3OE2ELMutex");
      }
    }

    else
    {
      //In case the active_flag is FALSE, then it is safe to suspend the task
      Serial.println("TASK: Suspend Task3");
      if ( xMutex != NULL ) {
        if (xSemaphoreTake( xMutex, portMAX_DELAY ) == pdTRUE) //if i was able to get the mutex (no other task is ussing the resource)
        {
          task_register[3].OE2EL = 0;
          task_register[3].last_end = 0; //assign latest end tasks value
          task_register[3].last_start = 0; //assign latest start tasks value for Task3
          task_register[3].state="SUSPENDED";
          xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it

        }
      }
      vTaskSuspend(NULL);
    }

    vTaskDelay( 300 / portTICK_PERIOD_MS );
  }
}
//TASK MODIFY: Add here any other tasks (clients or servers)

//********************************       END TASK DECLARATION       ***********************************************
//*****************************************************************************************************************



//********************************       EES TASK DECLARATION       ***********************************************
//*****************************************************************************************************************


void vTaskGetRunTimeStats( char *pcWriteBuffer )
{
TaskStatus_t *pxTaskStatusArray;
volatile UBaseType_t uxArraySize, x;
uint32_t ulTotalRunTime;
unsigned long ulStatsAsPercentage;

   /* Make sure the write buffer does not contain a string. */
   *pcWriteBuffer = 0x00;

   /* Take a snapshot of the number of tasks in case it changes while this
   function is executing. */
   uxArraySize = uxTaskGetNumberOfTasks();

   /* Allocate a TaskStatus_t structure for each task.  An array could be
   allocated statically at compile time. */
   pxTaskStatusArray = (TaskStatus_t *)pvPortMalloc( uxArraySize * sizeof( TaskStatus_t ) );

   if( pxTaskStatusArray != NULL )
   {
      /* Generate raw status information about each task. */
      uxArraySize = uxTaskGetSystemState( pxTaskStatusArray,
                                 uxArraySize,
                                 NULL );

      /* For percentage calculations. */
      ulTotalRunTime =1;

      /* Avoid divide by zero errors. */
      if( ulTotalRunTime > 0 )
      {
         /* For each populated position in the pxTaskStatusArray array,
         format the raw data as human readable ASCII data. */
         for( x = 0; x < uxArraySize; x++ )
         {
            /* What percentage of the total run time has the task used?
            This will always be rounded down to the nearest integer.
            ulTotalRunTimeDiv100 has already been divided by 100. */
            ulStatsAsPercentage =
                  pxTaskStatusArray[ x ].ulRunTimeCounter / ulTotalRunTime;

            if( ulStatsAsPercentage > 0UL )
            {
               sprintf( pcWriteBuffer, "%stt%lutt%lu%%rn",
                                 pxTaskStatusArray[ x ].pcTaskName,
                                 pxTaskStatusArray[ x ].ulRunTimeCounter,
                                 ulStatsAsPercentage );
            }
            else
            {
               /* If the percentage is zero here then the task has
               consumed less than 1% of the total run time. */
               sprintf( pcWriteBuffer, "%stt%lutt<1%%rn",
                                 pxTaskStatusArray[ x ].pcTaskName,
                                 pxTaskStatusArray[ x ].ulRunTimeCounter );
            }

            pcWriteBuffer += strlen( ( char * ) pcWriteBuffer );
         }
      }

      /* The array is no longer needed, free the memory it consumes. */
      vPortFree( pxTaskStatusArray );
   }
}



/*
  Declares RTOS task
  @param pvParameters RTOS
  @return void
*/
void SI_notifier(void *pvParameters)
{
  (void) pvParameters;

  uint16_t _OE2EL_T1 = 0, _OE2EL_T2 = 0, _OE2EL_T3 = 0;
  uint16_t _MAE2EL_T1 = 0, _MAE2EL_T2 = 0, _MAE2EL_T3 = 0;
  String _STATE_T1, _STATE_T2,_STATE_T3;
  // uint32_t xStart1, xEnd1, xDifference1;
  // uint32_t xStart2, xEnd2, xDifference2;

  //TASK MODIFY: Add here more variables for new tasks

  while (true) {

    uint8_t task_state = 255;
    String task_state_str = "";
    String SI_message = "";
    char *WriteBuffer;

    // xStart1 = xTaskGetTickCount();

    Serial.print("\nSI:\n\n");

    if ( xMutex != NULL ) {

      if (xSemaphoreTake( xMutex, portMAX_DELAY ) == pdTRUE) //if i was able to get the mutex (no other task is ussing the resource)
      {

        _OE2EL_T1 = task_register[1].OE2EL;
        _MAE2EL_T1 = task_register[1].MAE2EL;
        _STATE_T1= task_register[1].state;
        _OE2EL_T2 = task_register[2].OE2EL;
        _MAE2EL_T2 = task_register[2].MAE2EL;
        _STATE_T2= task_register[2].state;
        _OE2EL_T3 = task_register[3].OE2EL;
        _MAE2EL_T3 = task_register[3].MAE2EL;
        _STATE_T3= task_register[3].state;
        printTaskRegister();

        xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
      }
    }

    else {

      Serial.println("Error creating T1OE2ELMutex");
    }

    // vTaskGetRunTimeStats(WriteBuffer);
    // Serial.println(WriteBuffer);

    //TODO: Create the message in a loop
    //BUG: eTaskGetState and uxTaskPriorityGet for each tasks takes around 2 seconds to execute as it is a very heavy task.
    //
    task_state =  eTaskGetState(xHandleTask1_client);
    if (_OE2EL_T1 >= _MAE2EL_T1 * 2 && task_state != 3) {
      task_state = 5;
    }

    task_state_str = GetTaskStatus(task_state);
    SI_message = "{\"tasks\":{\"t1\":{\"id\":\"t1\",\"OE2EL\":" + String(_OE2EL_T1) + ",\"state\":\"" + task_state_str + "\"" + ",\"priority\":\"" + String(uxTaskPriorityGet( xHandleTask1_client )) + "\"},";

    task_state =  eTaskGetState(xHandleTask2_client);
    if (_OE2EL_T2 >= _MAE2EL_T2 * 2 && task_state != 3) {
      task_state = 5;
    }
    task_state_str = GetTaskStatus(task_state);
    SI_message = SI_message + "\"t2\":{\"id\":\"t2\",\"OE2EL\":" + String(_OE2EL_T2) + ",\"state\":\"" + task_state_str + "\"" + ",\"priority\":\"" + String(uxTaskPriorityGet( xHandleTask2_client )) + "\"},";

    task_state =  eTaskGetState(xHandleTask3_client);
    if (_OE2EL_T3 >= _MAE2EL_T3 * 2 && task_state != 3) {
      task_state = 5;
    }
    task_state_str = GetTaskStatus(task_state);
    SI_message = SI_message + "\"t3\":{\"id\":\"t3\",\"OE2EL\":" + String(_OE2EL_T3) + ",\"state\":\"" + task_state_str + "\"" + ",\"priority\":\"" + String(uxTaskPriorityGet( xHandleTask3_client )) + "\"}}}";

    
    // if (_OE2EL_T1 >= _MAE2EL_T1 * 2 && _STATE_T1 != "SUSPENDED") {
    //   _STATE_T1 = "TIMEOUT";
    // }
    // if (_OE2EL_T2 >= _MAE2EL_T2 * 2 && _STATE_T2 != "SUSPENDED") {
    //   _STATE_T2 = "TIMEOUT";
    // }
    // if (_OE2EL_T3 >= _MAE2EL_T3 * 2 && _STATE_T3 != "SUSPENDED") {
    //   _STATE_T3 = "TIMEOUT";
    // }

    // SI_message ="t1*"+ String(_OE2EL_T1)+"*"+_STATE_T1+"*"+String(uxTaskPriorityGet( xHandleTask1_client ))+
    // "&t2*"+ String(_OE2EL_T2)+"*"+_STATE_T2+"*"+String(uxTaskPriorityGet( xHandleTask2_client ))+
    // "&t3*"+ String(_OE2EL_T3)+"*"+_STATE_T3+"*"+String(uxTaskPriorityGet( xHandleTask3_client ));



    //TASK MODIFY: Add here the info of the new tasks to thew SI_message

    if (WiFi.status() == WL_CONNECTED) {
      // xStart2 = xTaskGetTickCount();
      HTTPClient http;
      http.begin(TASK_MONITOR_ISSUES_ENDPOINT);

      //http.begin(_TASK_MONITOR_ISSUES_ENDPOINT_,_TASK_MONITOR_ISSUES_ENDPOINT_PORT_,_TASK_MONITOR_ISSUES_ENDPOINT_PATH_);
      http.addHeader("Content-Type", "application/json");
      int httpResponseCode = http.POST(SI_message);

      if (httpResponseCode > 0) {

        //String response = http.getString(); //Get the response to the request
        //Serial.println(httpResponseCode);   //Print return code
        //Serial.println(response);           //Print request answer

      }

      else {

        Serial.print("Error on sending POST from SI: ");
        Serial.println(httpResponseCode);

      }

    }
    //Serial.println(SI_message);

    vTaskDelay( 100 / portTICK_PERIOD_MS );
  }
}







/*
  Declares RTOS task
  @param pvParameters RTOS
  @return void
*/
void TI_notifier(void *pvParameters)
{
  (void) pvParameters;

  while (true) {

    char Rx[LEN_MSG];
    //Serial.println("READING MESSAGE FROM QUEUE");
    if (xQueueReceive(queue_message, &Rx, 1000 / portTICK_RATE_MS) == pdTRUE) { //5s --> max time that the task is blocked if the queue is empty

      // if a message is in the queue, then notify the pes update to Task Monitor
      if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(TASK_MONITOR_PES_ENDPOINT);
        http.addHeader("Content-Type", "application/json");
        int httpResponseCode = http.POST(String(Rx));

        if (httpResponseCode > 0) {

          //String response = http.getString(); //Get the response to the request
          //Serial.println(httpResponseCode);   //Print return code
          //Serial.println(response);           //Print request answer

        }

        else {

          Serial.print("Error on sending POST from TI notifier to TaskMonitor: ");
          Serial.println(httpResponseCode);

        }
      }

    } else {
      Serial.println("Queue Timeout");
    }

    vTaskDelay( 100 / portTICK_PERIOD_MS );
  }
}
//******************************       END EES TASK DECLARATION       *********************************************
//*****************************************************************************************************************



/*
  Returns task scheduler state
  @param task state
  @return String
*/
String GetTaskStatus(uint8_t state) {
  String status_str = "NULL";
  switch (state)
  {
    case 0:
      status_str = "RUNNING";
      break;

    case 1:
      status_str = "READY";
      break;

    case 2:
      status_str = "BLOCKED";
      break;

    case 3:
      status_str = "SUSPENDED";
      break;

    case 4:
      status_str = "DELETED";
      break;

    case 5:
      status_str = "TIMEOUT";
      break;

    default:
      status_str = "NULL";
  }

  return status_str;
}



/*
  Returns all pes task information
  @param *request pointer to the request
  @return void
*/
void getAll(AsyncWebServerRequest *request)
{
  String message = "Get All pes";
  Serial.println(message);
  request->send(200, "text/plain", message);
}



/*
  Returns information for a given task
  @param
  @return void
*/
void getById(AsyncWebServerRequest *request)
{
  String id = GetInfoFromURL(request, "/pes/");
  String message = String("Get by Id ") + id;
  Serial.println(message);
  request->send(200, "text/plain", message);
}



/*
  Filter based on endpoint
  @param
  @return void
*/
void getRequest(AsyncWebServerRequest *request) {

  if (request->url().indexOf("/pes/") != -1)
  {
    getById(request);
  }
  else {
    getAll(request);
  }
}



/*
  [Task Interface] Implements the function to respond an HTTP POST on /pes-update endpoint
  @param *request, *data, data length,
  @return void
*/
void postPesUpdate(AsyncWebServerRequest * request, uint8_t *data, size_t len, size_t index, size_t total)
{
  //HTTPClient http2;
  //http2.begin(TASK_MONITOR_PES_ENDPOINT);
  String TI_message = "{\"id\":\"t1\",\"new_pes\":\"pes-local\"}";
  String current_pes;
  String bodyContent = GetBodyContent(data, len);
  //Serial.println(bodyContent);
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, bodyContent);

  if (error) {
    request->send(400);
    return;
  }

  String task_id = doc["task_id"];
  String new_pes = doc["pes"];
  String new_port = doc["port"];

  String message = "update pes for " + task_id + " migrating to: " + new_pes + " on port: " + new_port;
  request->send(200, "text/plain", message);
  //TODO: also must suspend server task here in case it was not suspended already
  // We could also need to resume the local task
  // if we delete the task we save resources but will need to reassign them once the task is to be created again
  //TODO: check if DM logic is able to ask to suspend a local task
  Serial.println(message);
  if (xSemaphoreTake( xMutex, portMAX_DELAY ) == pdTRUE) //if i was able to get the mutex (no other task is ussing the resource)
  {
    if (task_id == "t1") {

      if (new_pes == LOCAL_ADRESS || new_pes == "") {

        task_register[1].pes = LOCAL_ADRESS;
        task_register[1].port = GetTaskConfigParameter("t1", "port").toInt();
        task_register[1].OE2EL = 0;
        current_pes = "pes_local";
      }
      else {

        task_register[1].pes = new_pes;
        task_register[1].port = new_port.toInt();
        task_register[2].OE2EL = 0;
        current_pes = "pes_edge";
      }
    }
    if (task_id == "t2") {

      if (new_pes == LOCAL_ADRESS || new_pes == "") {

        task_register[2].pes = LOCAL_ADRESS;
        task_register[2].port = GetTaskConfigParameter("t1", "port").toInt();
        task_register[2].OE2EL = 0;
        current_pes = "pes_local";
      }
      else {

        task_register[2].pes = new_pes;
        task_register[2].port = new_port.toInt();
        task_register[2].OE2EL = 0;
        current_pes = "pes_edge";
      }
    }



    //TASK MODIFY: Add the same validation for all other enhanced or native tasks

    TI_message = "{\"id\":\"" + task_id + "\",\"new_pes\":\"" + current_pes + "\"}";;
    Serial.println (TI_message);
    xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
  }
  //put message of pes update into a queue than will be read by TI_notifier task
  //as if we try to do it here, and for some reason TM Component is not running properly, the embedded device
  //will reboot constantly due to a POST request causing time out in the AsyncWebServer library
  char char_array[TI_message.length() + 1];
  TI_message.toCharArray(char_array, TI_message.length() + 1);
  //Serial.println("putting message into QUEUE");
  if (xQueueSendToBack(queue_message, &char_array, 1000 / portTICK_RATE_MS) != pdTRUE) { //1seg--> max time that the task is blocked if the queue is full
    //Serial.printf("error-> put pes update in queue\n");
  }
  else {
    //Serial.println("queue put -> OK");
  }

}



/*
  [Task Interface] Implements the function to respond an HTTP POST on /resume-task endpoint
  @param *request, *data, data length,
  @return void
*/
void resumeTask(AsyncWebServerRequest * request, uint8_t *data, size_t len, size_t index, size_t total)
{
  String bodyContent = GetBodyContent(data, len);
  uint8_t task_pos_in_register = 0;
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, bodyContent);
  if (error) {
    request->send(400);
    return;
  }

  String task_id = doc["task_id"];
  String type = doc["type"];
  String task_to_resume = task_id + "_" + type;
  String message = "resume: " + task_to_resume;
  Serial.print("task_to_resume: ");
  Serial.println(task_to_resume);
  if (getTaskHandler(task_to_resume) != NULL) {
    try {

      if ( xMutex != NULL ) {
        if (xSemaphoreTake( xMutex, portMAX_DELAY ) == pdTRUE) //if i was able to get the mutex (no other task is ussing the resource)
        {
          task_register[getTaskPosinRegister(task_to_resume)].active = true;
          Serial.println("active_flag set to True");
          xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
        }
      }
      vTaskResume(getTaskHandler(task_to_resume));
      request->send(200, "text/plain", message);
      if (xSemaphoreTake( xMutex, portMAX_DELAY ) == pdTRUE) //if i was able to get the mutex (no other task is ussing the resource)
      {

        task_pos_in_register = getTaskPosinRegister(task_to_resume);
        task_register[task_pos_in_register].OE2EL = 0;
        task_register[task_pos_in_register].last_start = 0;
        task_register[task_pos_in_register].last_end = 0;

        xSemaphoreGive(xMutex); // MUST give back the mutex so other tasks can get it
      }

      throw (0);
    }
    catch (int error_code) {
      request->send(304, "text/plain", "None");
    }
  }
  else {
    Serial.println("Task does not exist, thus cannot resume");
    request->send(400, "text/plain", "None");
  }

}



/*
  [Scheduler Interface] Communicates the scheduler to suspend the task specified in
  the request after /task/
  @param *request a pointer to the incomming request
  @return void
*/
void suspendTask(AsyncWebServerRequest *request) {
  uint8_t task_pos_in_register = 0;
  String id = GetInfoFromURL(request, "/suspend-task/");
  String message = String("Suspends ") + id;
  Serial.println(message);
  if (getTaskHandler(id) != NULL) {
    try {
      //vTaskSuspend(getTaskHandler(id));

      if ( xMutex != NULL ) {
        if (xSemaphoreTake( xMutex, portMAX_DELAY ) == pdTRUE) //if i was able to get the mutex (no other task is ussing the resource)
        {
          task_pos_in_register = getTaskPosinRegister(id);
          task_register[task_pos_in_register].active = false;
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
  else {
    Serial.println("Task does not exist, thus cannot suspend");
    request->send(400, "text/plain", "None");
  }
}



/*
  Gets the string after a give root endpoint
  @param *request a pointer to the incomming request
  @param root  the endpoint after which the param will be gotten
  @return The given string after root
*/
String GetInfoFromURL(AsyncWebServerRequest *request, String root)
{
  String string_id = "";
  string_id = request->url();
  string_id.replace(root, "");

  return string_id;
}



/*
  Concatenates raw http post request data into a single string object
  @param *data pointer to data,
  @param len data length
  @return Data cointained into a String object
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
  Method to connect to WiFi in STA mode. It can use an static IP defined in config.h
  @param useStaticIP false if network does not allow it
  @return void
*/
void ConnectWiFi_STA(bool useStaticIP)
{
  Serial.println("");
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  if (useStaticIP) WiFi.config(ip, gateway, subnet);
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
  Method to connect to WiFi in AP mode. It can use an static IP defined in config.h
  @param useStaticIP false if network does not allow it
  @return void
*/
void ConnectWiFi_AP(bool useStaticIP)
{
  Serial.println("");
  WiFi.mode(WIFI_AP);
  while (!WiFi.softAP(ssid, password))
  {
    Serial.println(".");
    delay(100);
  }
  if (useStaticIP) WiFi.softAPConfig(ip, gateway, subnet);

  Serial.println("");
  Serial.print("Init AP:\t");
  Serial.println(ssid);
  Serial.print("IP address:\t");
  Serial.println(WiFi.softAPIP());
}



/*
  Implements the welcome message in case of a Home request
  @param *request a pointer to the incomming request
  @return void
*/
void homeRequest(AsyncWebServerRequest *request) {
  request->send(200, "text/plain", "Hello from EE-A");
}



/*
  Implements a function in case the requested HTTP request is not found
  @param *request a pointer to the incomming request
  @return void
*/
void notFound(AsyncWebServerRequest *request) {
  request->send(404, "text/plain", "Not found");
}



/*
  Initialize REST API server
  @return void
*/
void InitServer()
{
  server.on("/", HTTP_GET, homeRequest); //name_of_endpoint,HTTP_method,function_to_be_triggered
  server.on("/pes", HTTP_GET, getRequest);
  server.on("/pes-update", HTTP_POST, [](AsyncWebServerRequest * request) {}, NULL, postPesUpdate);
  server.on("/resume-task", HTTP_POST, [](AsyncWebServerRequest * request) {}, NULL, resumeTask);
  server.on("/suspend-task", HTTP_DELETE, suspendTask);
  server.onNotFound(notFound);

  server.begin(); // server starts listening to HTTP requests
  Serial.println("HTTP server started");
}



void setup()
{
  Serial.begin(115200);
  while (!Serial) {
    delay(2);
  }
  Serial.println("  ");
  xMutex = xSemaphoreCreateMutex();
  queue_message = xQueueCreate(LEN_QUEUE, LEN_MSG);

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
    ,  2048
    ,  NULL
    ,  5
    ,  NULL);

  xTaskCreate(
    &TI_notifier
    ,  "TI_notifier"
    ,  2048
    ,  NULL
    ,  5
    ,  NULL);


}


void loop()
{
  vTaskDelay( 1000 / portTICK_PERIOD_MS );
}





