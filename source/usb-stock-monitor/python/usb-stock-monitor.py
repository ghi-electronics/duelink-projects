# Stock Monitor with USB LED Indicator
#
# This application polls stock prices from the Finnhub API.
#
# Behavior:
# - Reads stock price periodically
# - Compares the current price with the previous price
#
# States:
# - UP        -> Set DUELink LED to GREEN
# - DOWN      -> Set DUELink LED to RED
# - NO CHANGE -> (Optional) Set LED to BLUE or keep last state
#
# Hardware:
# - USB-connected DUELink device
# - Receives commands from PC to control LED


import requests
import time
from datetime import datetime
from DUELink.DUELinkController import DUELinkController


availablePort = DUELinkController.GetConnectionPort()
duelink = DUELinkController(availablePort) #Bluetooth COM port, change to user comport

# duelink = DUELinkController("/dev/ttyAMA0")

def SetLed(color):
    duelink.Engine.ExecuteCommand(f"SetLed(0,{color})")
    duelink.Engine.ExecuteCommand(f"SetLed(1,{color})")
    duelink.Engine.ExecuteCommand(f"SetLed(2,{color})")


# ARGB color values (match C# Color.ToArgb())
class Color:
    White = -1          # 0xFFFFFFFF
    Green = -16744448   # approximate ARGB for Green
    Red = -65536        # 0xFFFF0000


symbol = input("Enter stock symbol (e.g. AAPL): ").upper()

apiKey = "YOUR_API_KEY"
lastPrice = None

SetLed(Color.White)

while True:
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={apiKey}"
        response = requests.get(url)
        data = response.json()

        currentPrice = float(data["c"])

        if lastPrice is not None:
            if currentPrice > lastPrice:
                SetLed(Color.Green)
                print(f"{datetime.now()}: UP ({currentPrice})")

            elif currentPrice < lastPrice:
                SetLed(Color.Red)
                print(f"{datetime.now()}: DOWN ({currentPrice})")

            else:
                print(f"{datetime.now()}: NO CHANGE ({currentPrice})")
        else:
            print(f"{datetime.now()}: Initial Price = {currentPrice}")

        lastPrice = currentPrice

    except Exception as ex:
        print(f"Error: {ex}")

    time.sleep(5)  # 5 seconds
