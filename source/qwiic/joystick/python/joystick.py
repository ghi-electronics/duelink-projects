# In this projects:
# Read X,Y and button state each 500ms
import time
from DUELink.DUELinkController import DUELinkController

availablePort = DUELinkController.GetConnectionPort()
duelink = DUELinkController(availablePort)

def Initialize():
    duelink.Engine.ExecuteCommand("dim b0[4]")  # Store X and Y: 2 bytes for X, 2 bytes for Y
    duelink.Engine.ExecuteCommand("dim b1[1]")  # Button state: 1 byte
    duelink.Engine.ExecuteCommand("DLMode(5,0)")  # Switch to I2C downlink mode


x = 0
y = 0
btPressed = False


def ScaleToPercentInt(value):
    if value < 0:
        value = 0
    if value > 65535:
        value = 65535

    return (value * 100) // 65535


def ReadXY():
    global x, y

    data = bytearray(4)
    duelink.Engine.ExecuteCommand("dli2cwr(0x20,[0x03],b0)")
    time.sleep(0.05)

    duelink.Stream.ReadBytes("b0", data)

    # Convert to the [0...100] range
    x = ScaleToPercentInt((data[0] << 8) | data[1])
    y = ScaleToPercentInt((data[2] << 8) | data[3])

    time.sleep(0.05)


def ReadButton():
    global btPressed

    duelink.Engine.ExecuteCommand("dli2cwr(0x20,[0x07],b1)")
    time.sleep(0.05)

    state = bytearray(1)
    duelink.Stream.ReadBytes("b1", state)

    btPressed = (state[0] == 0)


Initialize()

while True:
    ReadXY()
    ReadButton()

    print(f"X: {x}, Y: {y}, Button Pressed: {btPressed}")

    time.sleep(1)
