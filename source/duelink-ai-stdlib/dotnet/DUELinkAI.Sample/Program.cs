// ============================================================
// DUELink AI Playground
// ------------------------------------------------------------
// This project connects DUELink with AI to create a
// natural-language hardware interface.
//
// You write:
//   "set pin 1 high"
//   "blink LED 500ms"
//   "read voltage"
//
// AI converts it into:
//   DWrite(1,1)
//   StatLed(500,500,0)
//   VRead(1)
//
// Think of this as:
//   ChatGPT → DUELink → Real Hardware
//
// Fast prototyping. Zero friction.
// ============================================================

// Note: This is a demonstration project. Not all DUELink stdlib APIs have been fully tested.

using GHIElectronics.DUELink;
using GHIElectronics.DUELink.AI;
using System;
using System.IO;
using System.Runtime.CompilerServices;
class Program
{
    static async System.Threading.Tasks.Task Main()
    {
        var availablePort = DUELinkController.GetConnectionPort();
        var duelink = new DUELinkController(availablePort);

        var jsonPath = GetProjectPath() + "\\..\\GHIElectronics.DUELink.AI\\json"; // where to save json files.

        var apiKey = "YOUR_API_KEY";
        var ai = new DuelinkAI(apiKey, jsonPath, duelink);

        //var ai = new DuelinkAI(apiKey, jsonPath, null); // null mean no talk to device

        while (true)
        {
            Console.Write("> ");
            var input = Console.ReadLine();
            var result = await ai.Run(input);

            foreach (var r in result)
                Console.WriteLine(r);
        }
    }
    static string GetProjectPath([CallerFilePath] string path = "")
    {
        return Path.GetDirectoryName(path)!;
    }


}
