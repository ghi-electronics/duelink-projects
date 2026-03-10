// Sample project:
//
// 1. Connect to an Azure IoT Hub device.
// 2. Receive messages from Azure IoT Hub.
// 3. Split incoming messages into individual commands.
// 4. Send commands one at a time to the DueSTEM device.
// Require Microsoft.Azure.Devices.Client (dotnet add package Microsoft.Azure.Devices.Client)
//
// Message example:
//  SetBulb(0x00FF00)
//  statled(100, 100, 10)
//  ServoSt(5, 90)
//  Clear(1)
//  TextS("Azura IoT", 0, 10, 2, 2, 2)
//  Line(0, 15, 22, 100, 22)
//  Text("Light Bulb: Green", 0, 10, 30)
//  Text("Servo P5: 90", 0, 10, 40)
//  Show()

using System.Text;
using GHIElectronics.DUELink;
using Microsoft.Azure.Devices.Client;
var availablePort = DUELinkController.GetConnectionPort();
var duelink = new DUELinkController(availablePort);

string connectionString =
    "connection_string";

var deviceClient = DeviceClient.CreateFromConnectionString(
    connectionString,
    TransportType.Mqtt);

Console.WriteLine("Connected to Azure IoT Hub");
Console.WriteLine("Waiting for commands...");

while (true)
{
    var message = await deviceClient.ReceiveAsync();

    if (message == null)
        continue;

    string command = Encoding.UTF8.GetString(message.GetBytes());

    Console.WriteLine($"Cloud command: {command}");

    ExecuteCommand(command);

    await deviceClient.CompleteAsync(message);
}

void ExecuteCommand(string messages)
{
    // Split commands by newline
    var cmds = messages.Split(
        new[] { "\r\n", "\n" },
        StringSplitOptions.RemoveEmptyEntries);

    foreach (var cmd in cmds)
    {
        var trimmed = cmd.Trim();

        if (trimmed.Length == 0)
            continue;

        duelink.Engine.ExecuteCommand(trimmed);
        Thread.Sleep(10);
    }
}