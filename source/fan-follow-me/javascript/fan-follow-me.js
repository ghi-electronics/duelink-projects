// In this project:
// Use a distance sensor to scan for and detect objects.
// If an object is detected closer than 15 cm, rotate the fan toward the object and turn the fan on.
// While the object is present within 15 cm, keep the fan on.
// If the object disappears or moves farther than 15 cm, turn the fan off.
// Note: The fan and two servo motors draw much power (higher 500mA) and may require an external power source using a Power Inject module:
// https://www.duelink.com/docs/products/adpwrinj-a
// Device setup:
// servo motor : address 1
// distance: address 2
// servo motor: address 3
// fan: address 4

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
var distance = 0;
var angle = 0;
var offset = 5;
var dir = 1;
var current_dev = 0;

async function SetAddress(add) {
    if (current_dev !== add) {
        current_dev = add;
        await duelink.Engine.ExecuteCommand(`sel(${current_dev})`);
    }
}

async function SetServo(servo, angle) {
    // Servo 1: controls distance angle
    // Servo 3: controls fan angle
    await SetAddress(servo);
    await duelink.Engine.ExecuteCommand(`servost(1,${angle})`);
}

async function SetFanSpeed(speed, angle) {
    if (angle !== -1)
        await SetServo(3, angle);

    await SetAddress(4);
    await duelink.Engine.ExecuteCommand(`fan(${speed})`);
}

async function Distance() {
    await SetAddress(2);

    var d = parseInt(await duelink.Engine.ExecuteCommand("distance()"));

    return d;
}

async function Scan(angle) {
    await SetServo(1, angle);

    return await Distance();
}

async function Setup() {
    await SetServo(1, 20);
    await SetFanSpeed(0, 20);
}

async function Loop() {
    while (true) {
        await sleep(100);
        distance = await Distance();
        await SetServo(1, angle);

        angle += (dir * offset);

        if (angle > 160) {
            dir = -1;
        }

        if (angle < 20) {
            dir = 1;
        }

        if (distance < 15 && distance > 0) {
            await SetFanSpeed(60, angle);

            while (distance < 15) {
                distance = await Distance();
                await sleep(90);
            }

            await SetFanSpeed(0, -1);
        }
    }
}

await Setup();
await Loop();