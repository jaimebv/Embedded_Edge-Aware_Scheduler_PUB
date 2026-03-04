#include <string.h>
#include <ESPAsyncWebServer.h>

String GetInfoFromURL(AsyncWebServerRequest *request, String root);

String GetBodyContent(uint8_t *data, size_t len);
