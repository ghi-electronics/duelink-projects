#In this sample:
# Pressure (kPa) is read from a pressure sensor, and displayed on a gauge using stepper motor P1.

import time
from DUELink.DUELinkController import DUELinkController

#Enable this if connect by USB port
availablePort = DUELinkController.GetConnectionPort()
duelink = DUELinkController(availablePort) #Bluetooth COM port, change to user comport

# Linux
# duelink = DUELinkController("/dev/ttyAMA0")

#variable
deviceAddress = 0
presssureValue = 0
currentGaugeValue = 0

# methods
def SelectDevice(address):
    global deviceAddress

    if deviceAddress != address:
        # Save bus traffic; only update select when the address is different
        deviceAddress = address
        duelink.Engine.ExecuteCommand(f"sel({deviceAddress})")


def SetGauge(value):
    global currentGaugeValue

    if value == currentGaugeValue or value < 0:
        return

    SelectDevice(1)

    target_step = StepFromValue(value)
    current_step = StepFromValue(currentGaugeValue)

    diff = target_step - current_step

    direction = 1 if diff >= 0 else 0

    duelink.Engine.ExecuteCommand(f"step_m1({direction},{abs(diff)})")

    currentGaugeValue = value


def ReadPressure():
    # Return pressure in kPa
    SelectDevice(2)
    ret = int(duelink.Engine.ExecuteCommand("kPa()"))

    return ret


def StepFromValue(value):
    # Default resolution is 400 steps
    # Reaching the value 100 on the gauge requires 275 steps
    return int(value * 2.75)


while True:

    presssure_temp = ReadPressure()

    if presssure_temp != presssureValue:
        presssureValue = presssure_temp
        SetGauge(presssureValue)

        # Debug only
        print(f"Kpa reading: {presssureValue}")

    time.sleep(0.05)
