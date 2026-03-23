#In this sample:

#Read events from the Minetest game
#Transfer events to the DUELink smart LED

import os
import time


from DUELink.DUELinkController import DUELinkController

availablePort = DUELinkController.GetConnectionPort()
duelink = DUELinkController(availablePort)

# The output file is saved in the bin folder. We just need to read from there.
# File name "gamepulse.txt" is defined in init.lua
path = r"C:\Minetest\luanti-5.15.1-win64\bin\gamepulse.txt"

lastPunch = 0
lasthp = 0

def InitWS2811(width, heigh):
    duelink.Engine.ExecuteCommand(f"dim a1[] = {{14,{width},{heigh},1}}")
    duelink.Engine.ExecuteCommand(f"GfxCfg(3, a1, {width},{heigh}, 1)")

    SetColor(0x000005)

def SetColor(color):
    duelink.Engine.ExecuteCommand(f"Clear({color}):show()")

def DrawHp(hp):
    duelink.Engine.ExecuteCommand(f"Clear(0):Text(\"{str(hp)}\",0xFF,0,0):show()")


InitWS2811(16, 16)

while True:
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                text = f.read()

            parts = text.strip().split(',')
            punch = 0
            hp = 0

            for p in parts:
                kv = p.split(':')
                if len(kv) != 2:
                    continue

                key = kv[0].strip()
                value = kv[1].strip()

                if key == "PUNCH":
                    try:
                        punch = int(value)
                    except:
                        pass

                elif key == "HP":
                    try:
                        hp = int(value)
                    except:
                        pass

            if lastPunch != punch or lasthp != hp:
                lastPunch = punch
                lasthp = hp
                print(f"Punch:{punch} | HP:{hp}")

                if punch == 1:
                    SetColor(0xFF0000)
                else:
                    DrawHp(hp)

        except:
            print("Sync problem, ignored")

    time.sleep(0.05)  # Faster and more responsive (50 ms)