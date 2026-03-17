# Project Overview:
# - Use the Dial to control the PC volume.
# - Display the current volume level on LED R16.
#
# Note:
# The application reads the value from the Dial module
# and directly applies it to the PC volume.
#
# Before running this code, make sure the dial knob
# is set to zero or a low value.


import time
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from DUELink.DUELinkController import DUELinkController


availablePort = DUELinkController.GetConnectionPort()
duelink = DUELinkController(availablePort) #Bluetooth COM port, change to user comport

# duelink = DUELinkController("/dev/ttyAMA0")

currentAddress = 0

def SelectDevice(deviceAddress):
    global currentAddress
    # Optimize the bus, reduce bus traffic
    # Do not send the command if the address is the same
    if currentAddress != deviceAddress:
        currentAddress = deviceAddress
        duelink.Engine.ExecuteCommand(f"sel({currentAddress})")
        time.sleep(0.002)  # 2 ms delay


def Dial():
    SelectDevice(1)
    ret = duelink.Engine.ExecuteCommand("Dial()")
    if (ret> 95): # sometime return 99, set 100
        ret = 100
    return int(ret)


def SetLed(led, value):
    SelectDevice(2)
    val = 1 if value else 0
    duelink.Engine.ExecuteCommand(f"SetLed({led},{val})")


def LedOff():
    SelectDevice(2)
    duelink.Engine.ExecuteCommand("LedOff()")


# --- GET AUDIO DEVICE (Windows) ---
device = AudioUtilities.GetSpeakers().EndpointVolume

# dial state
dial = -1
dial_tmp = 0

while True:
    dial_tmp = Dial()

    if abs(dial_tmp - dial) > 1:  # Remove noise
        dial = dial_tmp

        # Set volume (0.0 → 1.0)
        device.SetMasterVolumeLevelScalar(dial / 100.0, None)

        led_num = dial * 16 // 100

        for i in range(led_num):
            SetLed(i + 1, True)

        for i in range(led_num, 16):
            SetLed(i + 1, False)

    time.sleep(0.05)  # 50 ms
