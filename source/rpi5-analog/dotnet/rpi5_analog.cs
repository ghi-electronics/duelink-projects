// This sample runs on Python on Raspberry Pi 5 using the UART port ttyAMA0.
// In this sample:
// Use DuePi to extend additional I/O and analog.
// Moisture and light values are updated and displayed on the screen every second.
// The slider value is read and shown on the Qwiic LED Stick.

using GHIElectronics.DUELink;

var availablePort = DUELinkController.GetConnectionPort();
var duelink = new DUELinkController(availablePort);


var deviceAddress = 0;

void SelectDevice(int address) {
    if (deviceAddress != address) {
        // Saving the bus, only update select when different current address
        deviceAddress = address;
        duelink.Engine.ExecuteCommand($"sel({deviceAddress})");
    }
}
int ReadLight() {
    SelectDevice(1);
    var ret = (int)duelink.Engine.ExecuteCommand("Trunc(VRead(1) / (ReadVcc()) * 100)");
    return ret;
}

int ReadSoil() {
    SelectDevice(1);
    var adc = (int)duelink.Engine.ExecuteCommand("Aread(2)");
    return adc;// ret;

}

void Init() {
    SelectDevice(2);

    // Enable downlink i2c mode on device 2
    duelink.Engine.ExecuteCommand("dlmode(5,0)");

}

void SetLed(int led, int red, int green, int blue) {

    if (led <= 0 || led > 10) {
        return;
    }

    red = red & 0xFF;
    green = green & 0xFF;
    blue = blue & 0xFF;

    SelectDevice(2);
    duelink.Engine.ExecuteCommand($"dli2cwr(0x23,[0x71,{led},{red},{green},{blue}],0)");
    Thread.Sleep(1);
}

int ReadSlider() {
    SelectDevice(2);
    return (int)duelink.Engine.ExecuteCommand("Slide()");

}

void ClearScreen() {
    SelectDevice(1);
    duelink.Engine.ExecuteCommand("Clear(0)");
}
void DrawText(string text, int x, int y) {
    SelectDevice(1);
    duelink.Engine.ExecuteCommand($"TextS(\"{text}\", 1, {x}, {y},2,2)");
}
void FlushScreen() {
    SelectDevice(1);
    duelink.Engine.ExecuteCommand("Show()");
}


var slide = 0;
var light = 0;
var moisture = 0;

var light_tmp = 0;
var moisture_tmp = 0;
var slide_tmp = 0;

var last_read = DateTime.Now;

Init();

while (true) {
    var diff = (DateTime.Now - last_read).TotalMilliseconds;

    if (diff >= 1000) {
        // This update every 1 second or only read when no sliding detected
        light_tmp = ReadLight();
        moisture_tmp = ReadSoil();
        last_read = DateTime.Now;
    }

    slide_tmp = ReadSlider();

    if (Math.Abs(slide_tmp - slide) >= 2) {
        // Saving the bus, only set led when detect different values
        // sentitive diff <2: don't count (for the speed)
        slide = slide_tmp;

        if (slide_tmp % 10 != 0) {
            // 0: 0
            // 1,2,3,...9: led 1
            // 11,12,13,...19: led 2
            // ....
            // 90,91,92... 99: led 10
            slide_tmp += 10;
        }

        slide_tmp = slide_tmp / 10;
        
        for (var i = 1; i <= slide_tmp; i++) {
            SetLed(i, 5, 5, 5);
        }
        for (var i = slide_tmp + 1; i <= 10; i++) {
            SetLed(i, 0, 0, 0);
        }
        last_read = DateTime.Now;

    }


    if (moisture_tmp != moisture || light_tmp != light) {
        // Saving the bus, only draw led when detect different values
        moisture = moisture_tmp;
        light = light_tmp;
        ClearScreen();
        DrawText($"Light:{light}", 12, 0);

        DrawText($"Moisture:", 10, 20);
        DrawText($"{moisture}", 50, 40);
        FlushScreen();
    }

    Thread.Sleep(1);

}

