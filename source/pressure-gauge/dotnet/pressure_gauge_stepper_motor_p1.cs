// In this sample:
// Pressure (kPa) is read from a pressure sensor, and displayed on a gauge using stepper motor P1.

using GHIElectronics.DUELink;

var availablePort = DUELinkController.GetConnectionPort();
var duelink = new DUELinkController(availablePort);

var deviceAddress = 0;
var presssureValue = 0;
var currentGaugeValue = 0;

void SelectDevice(int address) {
    if (deviceAddress != address) {
        // Saving the bus, only update select when different current address
        deviceAddress = address;
        duelink.Engine.ExecuteCommand($"sel({deviceAddress})");
    }
}
void SetGauge(int value) {
    if (value == currentGaugeValue || value <0)
        return;

    SelectDevice(1);

    var target_step = StepFromValue(value);
    var current_step = StepFromValue(currentGaugeValue);

    var diff = target_step - current_step;

    var direction = diff >= 0 ? 1 : 0;

    duelink.Engine.ExecuteCommand($"step_m1({direction},{Math.Abs(diff)})");

    currentGaugeValue = value;
}

int ReadPressure() {
    // return kPa
    SelectDevice(2);
    var ret = (int)duelink.Engine.ExecuteCommand("kPa()");

    return ret;

}

int StepFromValue(int value) {
    // default resolution is 400 steps
    // reach to the value 100 on the gauge take 275 steps.
    return (int)(value * 2.75);
}


while (true) {
        
    var presssure_temp = ReadPressure();
    if (presssure_temp!= presssureValue) {
        presssureValue = presssure_temp;
        SetGauge(presssureValue);

        //Debug only
        Console.WriteLine($"Kpa reading: {presssureValue}");
    }

    Thread.Sleep(50);
}

