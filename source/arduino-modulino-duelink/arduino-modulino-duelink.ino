#include "Arduino_LED_Matrix.h"
#include <stdint.h>
#include <Modulino.h>
#include <Wire.h>
#include <DUELink.h>

ModulinoBuzzer buzzer;
TwoWireTransport transport(Wire1);
DUELink duelink(transport);

float Slide() {
    return duelink.Engine.ExecuteCommand("Slide()");
}

void setup() {
  Modulino.begin();
  buzzer.begin();
  Serial.begin(9600);
  Wire1.begin();
  duelink.Connect();
}

void loop() {
  static bool initialized = false;
    if (!initialized) {

        initialized = true;
    }

    char msg[64];
    snprintf(msg, sizeof(msg), "Value: %f", Slide());
    Serial.println(msg);

    buzzer.tone(Slide()*50, 100); // Frequency: 440Hz, Duration: 1000ms
  delay(10);
}