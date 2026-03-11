// In this sample:
// Get HighTemp()
// Need to install script from the link below to device:
// https://github.com/ghi-electronics/duelink-projects/blob/main/source/wireless-weather-hightemp/standalone/wireless-weather-hightemp.txt


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
async function IsWiFiConnected() {
    // Pin 5 goes low when WiFi is connected
    var ret = await duelink.Engine.ExecuteCommand("dread(5,1)");
    return parseInt(ret) === 0;
}

async function HighTemp() {
    var ret = await duelink.Engine.ExecuteCommand("HighTemp()");
    return ret;
}

// HighTemp() accesses the web and parses JSON, which could take up to 6 seconds
duelink.ReadTimeout = 6000;

async function main() {
    while (true) {
        if (!(await IsWiFiConnected())) {
            console.log("Wait for WiFi connection...");
            await sleep(1000);
            continue;
        }

        console.log(`High Temp: ${await HighTemp()}`);
    }
}

main();