// In this projects:
// Read X,Y and button state each 500ms
using System.Diagnostics;
using GHIElectronics.DUELink;

var availablePort = DUELinkController.GetConnectionPort();
var duelink = new DUELinkController(availablePort);
void Initialize() {
    duelink.Engine.ExecuteCommand("dim b0[4]"); //Store X,Y: 2 bytes for X, 2 bytes for Y
    duelink.Engine.ExecuteCommand("dim b1[1]"); //Button state: 1 byte
    duelink.Engine.ExecuteCommand("DLMode(5,0)"); //Switch to I2C downlink
}

var x = 0;
var y = 0;
var btPressed = false;

static int ScaleToPercentInt(int value) {
    if (value < 0) value = 0;
    if (value > 65535) value = 65535;

    return (value * 100) / 65535;
}
void ReadXY() {
    var data = new byte[4];
    duelink.Engine.ExecuteCommand($"dli2cwr(0x20,[0x03],b0)");
    Thread.Sleep(50);
    duelink.Stream.ReadBytes("b0", data);

    // convert to [0...100] range
    x = ScaleToPercentInt((data[0] << 8) | data[1]);
    y = ScaleToPercentInt((data[2] << 8) | data[3]) ;
    Thread.Sleep(50);

}

void ReadButton() {
    duelink.Engine.ExecuteCommand($"dli2cwr(0x20,[0x07],b1)");
    Thread.Sleep(50);
    var state = new byte[1];
    duelink.Stream.ReadBytes("b1", state);

    btPressed = (state[0] == 0);
}


Initialize();
while (true) {
    ReadXY();
    ReadButton();

    Console.WriteLine($"X: {x}, Y: {y}, Button Pressed: {btPressed}");

    Thread.Sleep(1000);
}


