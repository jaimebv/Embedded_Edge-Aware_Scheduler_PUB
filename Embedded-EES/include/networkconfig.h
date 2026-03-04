#include <WiFi.h>

#define TASK_MONITOR_ISSUES_ENDPOINT "http://YOUR_PC_IP:4999/tm/si/latest_data" //put here PC IP
#define TASK_MONITOR_PES_ENDPOINT "http://YOUR_PC_IP:4999/tm/ti/pes_update"    //put here PC IP
#define LOCAL_ADRESS "127.0.0.1"

const char* ssid     = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";
//const char* ssid     = "YOUR_SSID";//
//const char* password = "YOUR_PASSWORD";
const char* hostname = "ESP32_1";



IPAddress ip(192, 168, 1, 200);
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);