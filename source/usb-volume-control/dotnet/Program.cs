// Project Overview:
// - Use the Dial to control the PC volume.
// - Display the current volume level on LED R16.
//
// Note:
// The application reads the value from the Dial module
// and directly applies it to the PC volume.
//
// Before running this code, make sure the dial knob
// is set to zero or a low value.

using NAudio.CoreAudioApi;
using GHIElectronics.DUELink;
using System;

var availablePort = DUELinkController.GetConnectionPort();
var duelink = new DUELinkController(availablePort);

int currentAddress = 0;
void SelectDevice(int deviceAddress)
{
    // Optimize the bus, reduce bus traffic
    // No send command if address are same
    if (currentAddress != deviceAddress)
    {
        currentAddress = deviceAddress;
        duelink.Engine.ExecuteCommand($"sel({currentAddress})");
        Thread.Sleep(2); // give some delay
    }
}
int Dial()
{
    SelectDevice(1);

    var ret = duelink.Engine.ExecuteCommand("Dial()");
    return (int)ret;
}

void SetLed(int led, bool value)
{
    SelectDevice(2);
    var val = value ? 1 : 0;
    duelink.Engine.ExecuteCommand($"SetLed({led},{val})");
}

void LedOff()
{
    SelectDevice(2);
    duelink.Engine.ExecuteCommand("LedOff()");
}

// Get device
var enumerator = new MMDeviceEnumerator();
var device = enumerator.GetDefaultAudioEndpoint(DataFlow.Render, Role.Multimedia);

//// --- GET VOLUME ---
//float volume = device.AudioEndpointVolume.MasterVolumeLevelScalar;
//Console.WriteLine($"Current Volume: {volume * 100}%");

//// --- SET VOLUME (example: 30%) ---
//device.AudioEndpointVolume.MasterVolumeLevelScalar = 0.3f;


var dial = -1;
var dial_tmp = 0;

while (true)
{
    dial_tmp  = Dial();

    if (Math.Abs(dial_tmp - dial) > 1) // Remove noise 
    {
        dial = dial_tmp;

        device.AudioEndpointVolume.MasterVolumeLevelScalar = (float)(dial / 100.0);

        var led_num = dial * 16 / 100;
        for (int i = 0; i < led_num; i++)
        {
            SetLed(i + 1, true);
        }

        for (int i = led_num; i < 16; i++)
        {
            SetLed(i + 1, false);
        }

    }

    Thread.Sleep(50);

}