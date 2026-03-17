using System;
using System.Linq;
using NAudio.Wave;
using NAudio.Dsp;
using NAudio.CoreAudioApi;

using GHIElectronics.DUELink;
using System;

var availablePort = DUELinkController.GetConnectionPort();
var duelink = new DUELinkController(availablePort);

//duelink.ReadTimeout = TimeSpan.FromMilliseconds(10);

// ================= CONFIG =================
int fftLength = 1024;
int bands = 8;

// better distribution
int[] bandLimits = { 4, 8, 16, 32, 64, 128, 256, 512 };

// smoothing memory
float[] previous = new float[bands];

// shared output
int[] latestOutput = new int[bands];
object lockObj = new object();

// FFT buffer
Complex[] fftBuffer = new Complex[fftLength];
int fftPos = 0;

// ================= AUDIO =================
var device = new MMDeviceEnumerator()
    .GetDefaultAudioEndpoint(DataFlow.Render, Role.Multimedia);

var capture = new WasapiLoopbackCapture(device);

Console.WriteLine("Device: " + device.FriendlyName);
Console.WriteLine("Format: " + capture.WaveFormat);

// ================= AUDIO CALLBACK =================
capture.DataAvailable += (s, e) =>
{
    int bytesPerSample = capture.WaveFormat.BitsPerSample / 8;
    int channels = capture.WaveFormat.Channels;
    int blockAlign = bytesPerSample * channels;

    for (int i = 0; i < e.BytesRecorded; i += blockAlign)
    {
        float sample = 0;

        if (capture.WaveFormat.Encoding == WaveFormatEncoding.IeeeFloat)
        {
            sample = BitConverter.ToSingle(e.Buffer, i);
        }
        else if (capture.WaveFormat.BitsPerSample == 16)
        {
            short s1 = BitConverter.ToInt16(e.Buffer, i);
            sample = s1 / 32768f;
        }

        // FFT input
        fftBuffer[fftPos].X = (float)(sample *
            FastFourierTransform.HammingWindow(fftPos, fftLength));
        fftBuffer[fftPos].Y = 0;

        fftPos++;

        if (fftPos >= fftLength)
        {
            fftPos = 0;

            FastFourierTransform.FFT(true,
                (int)Math.Log(fftLength, 2.0),
                fftBuffer);

            float[] mag = new float[fftLength / 2];

            for (int j = 0; j < mag.Length; j++)
            {
                float m = (float)Math.Sqrt(
                    fftBuffer[j].X * fftBuffer[j].X +
                    fftBuffer[j].Y * fftBuffer[j].Y);

                mag[j] = m / fftLength;
            }

            ProcessSpectrum(mag);
        }
    }
};

// ================= PROCESS =================
void ProcessSpectrum(float[] mag)
{
    float[] led = new float[bands];

    for (int b = 0; b < bands; b++)
    {
        int start = (b == 0) ? 0 : bandLimits[b - 1];
        int end = bandLimits[b];

        float max = 0;
        float sum = 0;
        int count = 0;

        for (int i = start; i < end && i < mag.Length; i++)
        {
            float m = mag[i];
            sum += m;
            if (m > max) max = m;
            count++;
        }

        float avg = sum / Math.Max(count, 1);

        float v = Math.Max(max, avg * 1.5f);

        // soft floor
        v = Math.Max(v, 0.000001f);

        // ✅ tuned gain (NOT too big)
        v *= 20000f;

        // log scale
        v = (float)Math.Log10(1 + v);

        // ✅ moderate high boost
        float boost = 1.0f + b * 0.3f;
        v *= boost;

        // ✅ bass punch
        if (b <= 1)
            v *= 1.5f;

        // smoothing (important for 10 FPS)
        v = v * 0.25f + previous[b] * 0.75f;

        // decay
        float decay = 0.015f;
        if (v < previous[b])
            v = previous[b] - decay;

        previous[b] = v;

        v = Math.Clamp(v, 0f, 1f);

        led[b] = v;
    }

    // ================= PIXEL OUTPUT =================
    int[] output = new int[bands];

    for (int i = 0; i < bands; i++)
    {
        float v = led[i];

        // ✅ more contrast (important)
        v = (float)Math.Pow(v, 0.55);

        int height = (int)(v * 80);

        height = Math.Clamp(height, 0, 60);

        // avoid flicker
        if (height > 0 && height < 4)
            height = 4;

        output[i] = height;
    }

    lock (lockObj)
    {
        latestOutput = output;
    }
}

// ================= 10 FPS OUTPUT =================
var timer = new System.Timers.Timer(100); // 100 ms = 10 FPS
var isUpdate = false;
timer.Elapsed += (s, e) =>
{

    int[] snapshot;

    lock (lockObj)
    {
        snapshot = (int[])latestOutput.Clone();
    }

    if (isUpdate)
        return;

    isUpdate = true;

    // 👉 PRINT (or send to DUELink)
    //Console.WriteLine(string.Join(" ", snapshot));
    var cmd = $"Equalizer([{snapshot[0]},{snapshot[1]},{snapshot[2]},{snapshot[3]},{snapshot[4]},{snapshot[5]},{snapshot[6]},{snapshot[7]}])";
    duelink.Engine.ExecuteCommand(cmd);
    isUpdate = false;


};

timer.Start();

// ================= START =================
capture.StartRecording();
Console.ReadLine();
capture.StopRecording();

