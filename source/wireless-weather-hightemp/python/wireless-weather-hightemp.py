# In this sample:
# Get HighTemp()
# You need to install the script from the link below on the device:
# https://github.com/ghi-electronics/duelink-projects/blob/main/source/wireless-weather-hightemp/standalone/wireless-weather-hightemp.txt


import time
from datetime import datetime
from DUELink.DUELinkController import DUELinkController


availablePort = DUELinkController.GetConnectionPort()
duelink = DUELinkController(availablePort) #Bluetooth COM port, change to user comport

# duelink = DUELinkController("/dev/ttyAMA0")

def IsWiFiConnected():
    # Pin 5 goes low when WiFi is connected
    ret = duelink.Engine.ExecuteCommand("dread(5,1)")
    return int(ret) == 0

def HighTemp():
    ret = duelink.Engine.ExecuteCommand("HighTemp()")
    return ret

# HighTemp() accesses the web and parses JSON, which could take up to 6 seconds
duelink.ReadTimeout = 6

while True:
    if not IsWiFiConnected():
        print("Wait for WiFi connection...")
        time.sleep(1)
        continue

    print(f"High Temp: {HighTemp()}")
