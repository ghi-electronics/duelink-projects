# In this project:
# - Monitor PC system metrics (CPU, RAM, Disk) in real time
# - Update values every second
# - Send and display information as text on a DUELink screen 
# - Demonstrates USB-connected PC monitoring with lightweight rendering
# require: pip install psutil wmi


import time
import psutil
import wmi
from DUELink.DUELinkController import DUELinkController


availablePort = DUELinkController.GetConnectionPort()
duelink = DUELinkController(availablePort) #Bluetooth COM port, change to user comport

# duelink = DUELinkController("/dev/ttyAMA0")

def Init():
    if (duelink.Engine.ExecuteCommand("info(0)") == 0x010006):
        duelink.Engine.ExecuteCommand("Init(1,0)")
    else:
        duelink.Engine.ExecuteCommand("Init(0,0)")
    time.sleep(0.25)


def WrapText(text, screenWidth, charWidth=5.6):
    maxChars = int(screenWidth / charWidth)

    lines = []
    words = text.split(' ')

    currentLine = ""

    for word in words:
        if (len(currentLine) + len(word) + 1) > maxChars:
            if len(currentLine) > 0:
                lines.append(currentLine)

            if len(word) > maxChars:
                index = 0
                while index < len(word):
                    length = min(maxChars, len(word) - index)
                    lines.append(word[index:index + length])
                    index += length
                currentLine = ""
            else:
                currentLine = word
        else:
            if len(currentLine) == 0:
                currentLine = word
            else:
                currentLine += " " + word

    if len(currentLine) > 0:
        lines.append(currentLine)

    return lines


def DrawCircle(color, x, y, radius):
    duelink.Engine.ExecuteCommand(f"circle({color},{x},{y},{radius})")


def DrawLine(color, x1, y1, x2, y2):
    duelink.Engine.ExecuteCommand(f"line({color},{x1},{y1},{x2},{y2})")


def DrawText(text, color, x, y):
    duelink.Engine.ExecuteCommand(f"textS(\"{text}\",{color},{x},{y},1,1)")


def Clear(color):
    duelink.Engine.ExecuteCommand(f"Clear({color})")


def Show():
    duelink.Engine.ExecuteCommand("Show()")


# =====================
# INIT PERFORMANCE
# =====================
cpu_percent = 0
ram_percent = 0

disk_read_prev = psutil.disk_io_counters().read_bytes
disk_write_prev = psutil.disk_io_counters().write_bytes

Init()

# Get CPU name (WMI)
cpuName = ""
w = wmi.WMI()
for cpu in w.Win32_Processor():
    cpuName = cpu.Name


# =====================
# LOOP
# =====================
while True:
    time.sleep(1)

    # =====================
    # READ VALUES
    # =====================
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent

    disk_io = psutil.disk_io_counters()
    read = (disk_io.read_bytes - disk_read_prev) / 1024.0  # KB
    write = (disk_io.write_bytes - disk_write_prev) / 1024.0  # KB

    disk_read_prev = disk_io.read_bytes
    disk_write_prev = disk_io.write_bytes

    Clear(0)

    names = WrapText(cpuName, 100)
    y = 5

    for name in names:
        x = int((100 - len(name) * 6) / 2)
        DrawText(f"{name}", 0x00ffff, x, y)
        y += 10

    DrawText(f"CPU usage: {int(cpu)}%", 0x00ffff, 2, y)
    y += 10

    DrawText(f"RAM usage: {int(ram)}%", 0x00ffff, 2, y)
    y += 10

    if read > 999:
        read_mb = read / 1024
        DrawText(f"DISK read:{int(read_mb)}MB", 0x00ffff, 2, y)
    else:
        DrawText(f"DISK read:{int(read)}KB", 0x00ffff, 2, y)

    y += 10

    if write > 999:
        write_mb = write / 1024
        DrawText(f"DISK write:{int(write_mb)}MB", 0x00ffff, 2, y)
    else:
        DrawText(f"DISK write:{int(write)}KB", 0x00ffff, 2, y)

    Show()
