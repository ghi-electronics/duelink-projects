# In this project:
# Use a distance sensor to scan for and detect objects.
# If an object is detected closer than 15 cm, rotate the fan toward the object and turn the fan on.
# While the object is present within 15 cm, keep the fan on.
# If the object disappears or moves farther than 15 cm, turn the fan off.
# Note: The fan and two servo motors draw much power (higher 500mA) and may require an external power source using a Power Inject module:
# https://www.duelink.com/docs/products/adpwrinj-a
# Device setup:
# servo motor : address 1
# distance: address 2
# servo motor: address 3
# fan: address 4

import time
from datetime import datetime
from DUELink.DUELinkController import DUELinkController


availablePort = DUELinkController.GetConnectionPort()
duelink = DUELinkController(availablePort)


# methods and variables
distance = 0
angle = 0
offset = 5
dir = 1
current_dev = 0


def SetAddress(add):
    global current_dev
    if current_dev != add:
        current_dev = add
        duelink.Engine.ExecuteCommand(f"sel({current_dev})")


def SetServo(servo, angle):
    # Servo 1: controls distance angle
    # Servo 3: controls fan angle
    SetAddress(servo)
    duelink.Engine.ExecuteCommand(f"servost(1,{angle})")


def SetFanSpeed(speed, angle):
    if angle != -1:
        SetServo(3, angle)

    SetAddress(4)
    duelink.Engine.ExecuteCommand(f"fan({speed})")


def Distance():
    SetAddress(2)

    d = int(duelink.Engine.ExecuteCommand("distance()"))

    return d


def Scan(angle):
    SetServo(1, angle)

    return Distance()


def Setup():
    SetServo(1, 20)
    SetFanSpeed(0, 20)


def Loop():
    global distance, angle, dir

    while True:
        time.sleep(0.1)
        distance = Distance()
        SetServo(1, angle)

        angle += (dir * offset)

        if angle > 160:
            dir = -1

        if angle < 20:
            dir = 1

        if distance < 15 and distance > 0:
            SetFanSpeed(60, angle)

            while distance < 15:
                distance = Distance()
                time.sleep(0.08)

            SetFanSpeed(0, -1)


Setup()
Loop()
