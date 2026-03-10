# Sample project:
#
# 1. Connect to an Azure IoT Hub device.
# 2. Receive messages from Azure IoT Hub.
# 3. Split incoming messages into individual commands.
# 4. Send commands one at a time to the DueSTEM device.
# Requires: pip install azure-iot-device
#
# Message example:
#  SetBulb(0x00FF00)
#  statled(100, 100, 10)
#  ServoSt(5, 90)
#  Clear(1)
#  TextS("Azure IoT", 0, 10, 2, 2, 2)
#  Line(0, 15, 22, 100, 22)
#  Text("Light Bulb: Green", 0, 10, 30)
#  Text("Servo P5: 90", 0, 10, 40)
#  Show()

import asyncio
import time
from azure.iot.device.aio import IoTHubDeviceClient
from DUELink.DUELinkController import DUELinkController

#Enable this if connect by USB port
availablePort = DUELinkController.GetConnectionPort()
duelink = DUELinkController(availablePort) #Bluetooth COM port, change to user comport

# Linux
# duelink = DUELinkController("/dev/ttyAMA0")

#variable
connectionString = "connection_string"

deviceClient = IoTHubDeviceClient.create_from_connection_string(connectionString)


async def main():
    await deviceClient.connect()

    print("Connected to Azure IoT Hub")
    print("Waiting for commands...")

    while True:
        message = await deviceClient.receive_message()

        if message is None:
            continue

        command = message.data.decode("utf-8")

        print(f"Cloud command: {command}")

        ExecuteCommand(command)


def ExecuteCommand(messages):
    # Split commands by newline
    cmds = [c.strip() for c in messages.splitlines() if c.strip()]

    for cmd in cmds:
        duelink.Engine.ExecuteCommand(cmd)
        time.sleep(0.01)


asyncio.run(main())
