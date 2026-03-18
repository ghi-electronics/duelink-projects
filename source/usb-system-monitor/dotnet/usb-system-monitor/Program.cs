// In this project:
// - Monitor PC system metrics (CPU, RAM, Disk) in real time
// - Update values every second
// - Send and display information as text on a 106x80 DUELink screen
// - Demonstrates USB-connected PC monitoring with lightweight rendering

using GHIElectronics.DUELink;
using System.Diagnostics;
using System.Management;

var availablePort = DUELinkController.GetConnectionPort();
var duelink = new DUELinkController(availablePort);

void Init()
{
    if (duelink.Engine.ExecuteCommand("info(0)") == 0x010006)
        duelink.Engine.ExecuteCommand("Init(1,0)");
    else
        duelink.Engine.ExecuteCommand("Init(0,0)");
    Thread.Sleep(250);
}

// =====================
// INIT PERFORMANCE
// =====================
var cpuCounter = new PerformanceCounter("Processor", "% Processor Time", "_Total");
var ramCounter = new PerformanceCounter("Memory", "% Committed Bytes In Use");
var diskRead = new PerformanceCounter("PhysicalDisk", "Disk Read Bytes/sec", "_Total");
var diskWrite = new PerformanceCounter("PhysicalDisk", "Disk Write Bytes/sec", "_Total");

Init();

cpuCounter.NextValue();
diskRead.NextValue();
diskWrite.NextValue();

var cpuName = "";
var searcher = new ManagementObjectSearcher("select Name from Win32_Processor");
foreach (var item in searcher.Get())
{
    cpuName = item["Name"].ToString();
}

// =====================
// LOOP
// =====================
while (true)
{
    Thread.Sleep(1000);

    

    // =====================
    // READ VALUES
    // =====================
    float cpu = cpuCounter.NextValue();
    float ram = ramCounter.NextValue();

    float read = diskRead.NextValue();
    float write = diskWrite.NextValue();
    float disk = (read + write) / 1024f; // KB/s

   
    Clear(0);


    var names = WrapText(cpuName, 100);
    var count = 0;
    var y = 5;
    foreach (var name in names)
    {
        var x = (100 - name.Length * 6) / 2;
        DrawText($"{name}", 0x00ffff, x, y);
        count++;
        y += 10;
    }

    DrawText($"CPU usage: {cpu:F0}%", 0x00ffff,2, y); 
    y += 10;
    DrawText($"RAM usage: {ram:F0}%", 0x00ffff, 2, y); 
    y += 10;
    if (read > 999)
    {
        read /= 1024;
        DrawText($"DISK read:{(int)read:F0}MB", 0x00ffff, 2, y); 
    }
    else
    {
        DrawText($"DISK read:{(int)read:F0}KB", 0x00ffff, 2, y);
    }
    y += 10;

    if (write > 999)
    {
        write /= 1024;
        DrawText($"DISK write:{(int)write:F0}MB", 0x00ffff, 2, y);
    }
    else
    {
        DrawText($"DISK write:{(int)write:F0}KB", 0x00ffff, 2, y);
    }

    Show();
}

string[] WrapText(string text, int screenWidth, float charWidth = 5.6f)
{
    int maxChars = (int)(screenWidth / charWidth);

    var lines = new List<string>();
    var words = text.Split(' ');

    string currentLine = "";

    foreach (var word in words)
    {
        // If adding this word exceeds line
        if ((currentLine.Length + word.Length + 1) > maxChars)
        {
            // Push current line
            if (currentLine.Length > 0)
                lines.Add(currentLine);

            // If word itself too long → split it
            if (word.Length > maxChars)
            {
                int index = 0;
                while (index < word.Length)
                {
                    int len = (int)Math.Min(maxChars, word.Length - index);
                    lines.Add(word.Substring(index, len));
                    index += len;
                }

                currentLine = "";
            }
            else
            {
                currentLine = word;
            }
        }
        else
        {
            if (currentLine.Length == 0)
                currentLine = word;
            else
                currentLine += " " + word;
        }
    }

    // Add last line
    if (currentLine.Length > 0)
        lines.Add(currentLine);

    return lines.ToArray();
}

// =====================
// FUNCTIONS
// =====================

void DrawCircle(int color, int x, int y, int radius)
{
    duelink.Engine.ExecuteCommand($"circle({color},{x},{y},{radius})");
}

void DrawLine(int color, int x1, int y1, int x2, int y2)
{
    duelink.Engine.ExecuteCommand($"line({color},{x1},{y1},{x2},{y2})");
}

void DrawText(string text, int color, int x, int y)
{
    duelink.Engine.ExecuteCommand($"textS(\"{text}\",{color},{x},{y},1,1)");
}

void Clear(int color)
{
    duelink.Engine.ExecuteCommand($"Clear({color})");
}

void Show()
{
    duelink.Engine.ExecuteCommand("Show()");
}



