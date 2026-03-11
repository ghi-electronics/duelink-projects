// In this sample:
// Get HighTemp()
// Need to install script from the link below to device:
// https://github.com/ghi-electronics/duelink-projects/blob/main/source/wireless-weather-hightemp/standalone/wireless-weather-hightemp.txt

using GHIElectronics.DUELink;

var availablePort = DUELinkController.GetConnectionPort();
var duelink = new DUELinkController(availablePort);

bool IsWiFiConnected() {
    // Pin 5 goes low when WiFi is connected
    var ret = duelink.Engine.ExecuteCommand("dread(5,1)");
    return (int)ret == 0;
}

float HighTemp() {
    var ret = duelink.Engine.ExecuteCommand("HighTemp()");
    return ret;
}

// # HighTemp() accesses the web and parses JSON, which could take up to 6 seconds
duelink.ReadTimeout = TimeSpan.FromSeconds(6);
while (true) {
    if (!IsWiFiConnected()) {
        Console.WriteLine("Wait for FiFi connection...");
        Thread.Sleep(1000);
        continue;
    }

    Console.WriteLine($"High Temp: {HighTemp()}");
}


