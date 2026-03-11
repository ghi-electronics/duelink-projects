// This sample runs on DueDuino

// In this sample:
// Get HighTemp()
// Need to install the script from the link below on the device:
// https://github.com/ghi-electronics/duelink-projects/blob/main/source/wireless-weather-hightemp/standalone/wireless-weather-hightemp.txt

#include <Arduino.h>
#include <DUELink.h>

SerialTransport transport(Serial2);
DUELink duelink(transport);

bool IsWiFiConnected() {
    // Pin 5 goes low when WiFi is connected
    float ret = duelink.Engine.ExecuteCommand("dread(5,1)");
    return ((int)ret) == 0;
}

float HighTemp() {
    float ret = duelink.Engine.ExecuteCommand("HighTemp()");
    return ret;
}

void setup() {
    Serial2.begin(115200);
    duelink.Connect();
}

void loop() {
    if (!IsWiFiConnected()) {        
        delay(1000);
        return;
    }

    float temp = HighTemp();

    // Show temp to output
}