# This project connects DUELink with AI to create a
# natural-language hardware interface.
#
# You write:
#   "set pin 1 high"
#   "blink LED 500ms"
#   "read voltage"
#
# AI converts it into:
#   DWrite(1,1)
#   StatLed(500,500,0)
#   VRead(1)
#
# Think of this as:
#   ChatGPT → DUELink → Real Hardware
#
# Fast prototyping. Zero friction.
# ============================================================

# Note: This is a demonstration project. Not all DUELink stdlib APIs have been fully tested.
# need asyncio: pip install aiohttp
# need asyncio: pip install duelink

import os
import asyncio 
from duelink_ai.duelink_ai import DuelinkAI

from DUELink.DUELinkController import DUELinkController 



availablePort = DUELinkController.GetConnectionPort()
duelink = DUELinkController(availablePort)
jsonPath = os.getcwd() + "/duelink_ai/json"
apiKey = "YOUR_API_KEY"


async def main():
    if not os.path.isdir(jsonPath):
        print("Folder not exists")
        return

    ai = DuelinkAI(
        key=apiKey,
        jsonPath=jsonPath,   
        duelink=duelink
    )

    print("DUELink AI Ready")

    while True:
        prompt = input("> ")

        results = await ai.Run(prompt)

        for r in results:
            print(r)


asyncio.run(main())