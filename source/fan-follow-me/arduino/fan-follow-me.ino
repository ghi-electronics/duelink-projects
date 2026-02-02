// This sample runs on Arduino UNO 4 WIFI
// In this project:
// Use a distance sensor to scan for and detect objects.
// If an object is detected closer than 15 cm, rotate the fan toward the object and turn the fan on.
// While the object is present within 15 cm, keep the fan on.
// If the object disappears or moves farther than 15 cm, turn the fan off.
// Note: The fan and two servo motors draw much power (higher 500mA) and may require an external power source using a Power Inject module:
// https://www.duelink.com/docs/products/adpwrinj-a
// Device setup:
// servo motor : address 1
// distance: address 2
// servo motor: address 3
// fan: address 4

#include <Arduino.h>
#include <Wire.h>
#include <DUELink.h>

TwoWireTransport transport(Wire1);
DUELink duelink(transport);

int distance = 0;
int angle = 0;
int offset = 5;
int dir = 1;
int current_dev = 0;

void SetAddress(int add) {
    if (current_dev != add) {
        current_dev = add;
        char cmd[64];
        int tmp = transport.ReadTimeout;
        transport.ReadTimeout = 50;
        snprintf(cmd, sizeof(cmd), "sel(%d)", current_dev);
        duelink.Engine.ExecuteCommand(cmd);
        transport.ReadTimeout = tmp;
    }
}

void SetServo(int servo, int angleValue) {
    // Servo 1: control distance degree
    // Servo 3: control fan degree
    SetAddress(servo);
    char cmd[64];
    snprintf(cmd, sizeof(cmd), "servost(1,%d)", angleValue);
    duelink.Engine.ExecuteCommand(cmd);
}

void SetFanSpeed(int speed, int angleValue) {
    if (angleValue != -1) {
        SetServo(3, angleValue);
    }

    SetAddress(4);
    char cmd[64];
    snprintf(cmd, sizeof(cmd), "fan(%d)", speed);
    duelink.Engine.ExecuteCommand(cmd);
}

int Distance() {
    SetAddress(2);
    float d = duelink.Engine.ExecuteCommand("distance()");
    return (int)d;
}

int Scan(int angleValue) {
    SetServo(1, angleValue);
    return Distance();
}

void setup() {
    Serial.begin(9600);
    Wire1.begin();
    duelink.Connect();

    SetServo(1, 20);
    SetFanSpeed(0, 20);
}

void loop() {
    delay(100);

    distance = Distance();
    SetServo(1, angle);

    angle += (dir * offset);

    if (angle > 160) {
        dir = -1;
    }

    if (angle < 20) {
        dir = 1;
    }

    if (distance < 15 && distance > 0) {
        SetFanSpeed(80, angle);

        while (distance < 15) {
            distance = Distance();
            delay(80);
        }

        SetFanSpeed(0, -1);
    }
}
