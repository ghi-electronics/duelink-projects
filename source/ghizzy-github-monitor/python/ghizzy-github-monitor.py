# 🚀 Ghizzy GitHub Build Monitor
# Monitor GitHub Actions:
# When there is no build: Ghizzy's eye color is blue.
# When the build succeeds: Ghizzy's eye color is green.
# When the build fails: Ghizzy's eye color is red.
# When building or commit: Ghizzy's eyes blink, the mouth blinks, and a beep sound is played.

import requests
import threading
import time
from DUELink.DUELinkController import DUELinkController


availablePort = DUELinkController.GetConnectionPort()
duelink = DUELinkController(availablePort) #Bluetooth COM port, change to user comport

# duelink = DUELinkController("/dev/ttyAMA0")

owner = "your_github_repo"
repo = "your_project"
# repo = "duelink-projects"
token = "your_token"

intervalSeconds = 10

headers = {
    "User-Agent": "BuildMonitor/1.0",
    "Authorization": f"Bearer {token}"
}

lastState = ""
lastState_tmp = "NO_BUILD"
lastCommitSha = ""


def GetLatestCommitSha():
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=1"

    response = requests.get(url, headers=headers)
    data = response.json()

    if len(data) == 0:
        return ""

    return data[0].get("sha", "")


def GetBuildState():
    global lastCommitSha

    # 🔥 Always check commit first
    latestSha = GetLatestCommitSha()

    if lastCommitSha != "" and latestSha != lastCommitSha:
        lastCommitSha = latestSha
        return "NEW_COMMIT"

    lastCommitSha = latestSha

    # Then check Actions
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page=1"

    response = requests.get(url, headers=headers)
    data = response.json()

    runs = data.get("workflow_runs", [])

    if len(runs) == 0:
        return "NO_BUILD"

    run = runs[0]

    status = run.get("status")
    conclusion = run.get("conclusion")

    if status in ["queued", "in_progress"]:
        return "BUILDING"

    if status == "completed":
        if conclusion == "success":
            return "SUCCESS"
        else:
            return "FAILED"

    return "NO_BUILD"


def SetLedThread():
    global lastState, lastState_tmp

    counter = 0

    while True:
        if lastState_tmp != lastState:
            lastState_tmp = lastState

            if lastState == "SUCCESS":
                duelink.Engine.ExecuteCommand(f"LEye(0,255,0)")
                duelink.Engine.ExecuteCommand(f"REye(0,255,0)")
                duelink.Engine.ExecuteCommand(f"Mouth(0,0,0)")
                duelink.Engine.ExecuteCommand(f"SetEar(0,0)")

            elif lastState == "FAILED":
                duelink.Engine.ExecuteCommand(f"LEye(255,0,0)")
                duelink.Engine.ExecuteCommand(f"REye(255,0,0)")
                duelink.Engine.ExecuteCommand(f"Mouth(0,0,0)")
                duelink.Engine.ExecuteCommand(f"SetEar(0,0)")

            elif lastState == "NO_BUILD":
                duelink.Engine.ExecuteCommand(f"LEye(0,0,255)")
                duelink.Engine.ExecuteCommand(f"REye(0,0,255)")
                duelink.Engine.ExecuteCommand(f"Mouth(0,0,0)")
                duelink.Engine.ExecuteCommand(f"SetEar(0,0)")

            elif lastState == "NEW_COMMIT":

                for i in range(10):
                    eye = 50 if i % 2 == 0 else 0
                    mouth = 0 if i % 2 == 0 else 50

                    duelink.Engine.ExecuteCommand("freq(3,2000,50,0.5)")
                    duelink.Engine.ExecuteCommand(f"LEye({eye},{eye},{eye})")
                    duelink.Engine.ExecuteCommand(f"REye({eye},{eye},{eye})")
                    duelink.Engine.ExecuteCommand(f"SetEar({mouth},{mouth})")
                    duelink.Engine.ExecuteCommand(f"Mouth({mouth},{mouth},{mouth})")

                    time.sleep(0.1)  # 100 ms

        if lastState == "BUILDING":
            eye = 50 if counter % 2 == 0 else 0
            mouth = 0 if counter % 2 == 0 else 50

            duelink.Engine.ExecuteCommand("freq(3,2000,50,0.5)")
            duelink.Engine.ExecuteCommand(f"LEye({eye},{eye},{eye})")
            duelink.Engine.ExecuteCommand(f"REye({eye},{eye},{eye})")
            duelink.Engine.ExecuteCommand(f"Mouth({mouth},{mouth},{mouth})")

        counter += 1
        time.sleep(0.05)  # 50 ms


# Start LED thread
threading.Thread(target=SetLedThread, daemon=True).start()

# Main loop
while True:
    try:
        lastState = GetBuildState()
    except Exception as ex:
        print("Error:", ex)

    time.sleep(intervalSeconds)
