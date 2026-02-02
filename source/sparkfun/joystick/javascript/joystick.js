// In this projects:
// Read X,Y and button state each 500ms

import pkg_serialusb from 'dlserialusb';
const {SerialUSB} = pkg_serialusb

import pkg_duelink from 'duelink';
const {DUELinkController} = pkg_duelink

let duelink = new DUELinkController(new SerialUSB());
await duelink.Connect();

// Sleep helper (ms)
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Methods
async function Initialize() {
    await duelink.Engine.ExecuteCommand("dim b0[4]"); // Store X and Y: 2 bytes for X, 2 bytes for Y
    await duelink.Engine.ExecuteCommand("dim b1[1]"); // Button state: 1 byte
    await duelink.Engine.ExecuteCommand("DLMode(5,0)"); // Switch to I2C downlink mode
}

let x = 0;
let y = 0;
let btPressed = false;

async function ScaleToPercentInt(value) {
    if (value < 0) value = 0;
    if (value > 65535) value = 65535;

    return Math.floor((value * 100) / 65535);
}

async function ReadXY() {
    const data = new Uint8Array(4);

    await duelink.Engine.ExecuteCommand("dli2cwr(0x20,[0x03],b0)");
    await sleep(50);

    await duelink.Stream.ReadBytes("b0", data);

    // Convert to the [0...100] range
    x = await ScaleToPercentInt((data[0] << 8) | data[1]);
    y = await ScaleToPercentInt((data[2] << 8) | data[3]);

    await sleep(50);
}

async function ReadButton() {
    await duelink.Engine.ExecuteCommand("dli2cwr(0x20,[0x07],b1)");
    await sleep(50);

    const state = new Uint8Array(1);
    await duelink.Stream.ReadBytes("b1", state);

    btPressed = (state[0] === 0);
}

(async function main() {
    await Initialize();

    while (true) {
        await ReadXY();
        await ReadButton();

        console.log(`X: ${x}, Y: ${y}, Button Pressed: ${btPressed}`);

        await sleep(1000);
    }
})();