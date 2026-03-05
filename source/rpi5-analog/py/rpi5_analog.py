
# This sample runs on Python on Raspberry Pi 5 using the UART port ttyAMA0.
# In this sample:
# Use DuePi to extend additional I/O and analog.
# Moisture and light values are updated and displayed on the screen every second.
# The slider value is read and shown on the Qwiic LED Stick.

import time
from datetime import datetime
from DUELink.DUELinkController import DUELinkController

#Enable this if connect by USB port
#availablePort = DUELinkController.GetConnectionPort()
#duelink = DUELinkController(availablePort) #Bluetooth COM port, change to user comport

duelink = DUELinkController("/dev/ttyAMA0")

#variable
deviceAddress = 0
# methods

def SelectDevice(address):
    global deviceAddress
    if deviceAddress != address:
        # Save bus traffic, only update selection when the address changes
        deviceAddress = address
        duelink.Engine.ExecuteCommand(f"sel({deviceAddress})")


def ReadLight():
    SelectDevice(1)
    ret = int(duelink.Engine.ExecuteCommand("Trunc(VRead(1)/(ReadVcc())*100)"))
    return ret


def ReadSoil():
    SelectDevice(1)
    adc = int(duelink.Engine.ExecuteCommand("Aread(2)"))
    return adc  # ret


def Init():
    SelectDevice(2)

    # Enable downlink I2C mode on device 2
    duelink.Engine.ExecuteCommand("dlmode(5,0)")


def SetLed(led, red, green, blue):

    if led <= 0 or led > 10:
        return

    red = red & 0xFF
    green = green & 0xFF
    blue = blue & 0xFF

    SelectDevice(2)
    duelink.Engine.ExecuteCommand(f"dli2cwr(0x23,[0x71,{led},{red},{green},{blue}],0)")
    time.sleep(0.005)


def ReadSlider():
    SelectDevice(2)
    return int(duelink.Engine.ExecuteCommand("Slide()"))


def ClearScreen():
    SelectDevice(1)
    duelink.Engine.ExecuteCommand("Clear(0)")


def DrawText(text, x, y):
    SelectDevice(1)
    duelink.Engine.ExecuteCommand(f'TextS("{text}", 1, {x}, {y},2,2)')


def FlushScreen():
    SelectDevice(1)
    duelink.Engine.ExecuteCommand("Show()")


slide = 0
light = 0
moisture = 0

light_tmp = 0
moisture_tmp = 0
slide_tmp = 0

last_read = datetime.now()

Init()

while True:

    diff = (datetime.now() - last_read).total_seconds() * 1000

    if diff >= 1000:
        # Update every 1 second or only read when no sliding is detected
        light_tmp = ReadLight()
        moisture_tmp = ReadSoil()
        last_read = datetime.now()

    slide_tmp = ReadSlider()

    if abs(slide_tmp - slide) >= 2:
        # Save bus traffic, only update LEDs when different values are detected
        # Small differences <2 are ignored (for speed)
        slide = slide_tmp

        if slide_tmp % 10 != 0:
            # 0: 0
            # 1,2,3,...9: led 1
            # 11,12,13,...19: led 2
            # ....
            # 90,91,92...99: led 10
            slide_tmp += 10

        slide_tmp = slide_tmp // 10

        for i in range(1, slide_tmp + 1):
            SetLed(i, 5, 5, 5)

        for i in range(slide_tmp + 1, 11):
            SetLed(i, 0, 0, 0)

        last_read = datetime.now()

    if moisture_tmp != moisture or light_tmp != light:
        # Save bus traffic, only redraw the screen when values change
        moisture = moisture_tmp
        light = light_tmp

        ClearScreen()
        DrawText(f"Light:{light}", 12, 0)

        DrawText("Moisture:", 10, 20)
        DrawText(f"{moisture}", 50, 40)

        FlushScreen()

    time.sleep(0.001)
