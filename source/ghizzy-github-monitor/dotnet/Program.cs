// In this project:
// Monitor GitHub Actions:
// When there is no build: Ghizzy's eye color is blue.
// When the build succeeds: Ghizzy's eye color is green.
// When the build fails: Ghizzy's eye color is red.
// When building: Ghizzy's eyes blink, the mouth blinks, and a beep sound is played.

using GHIElectronics.DUELink;
using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;

var availablePort = DUELinkController.GetConnectionPort();
var duelink = new DUELinkController(availablePort);

string owner = "your_github_repo";
string repo = "your_project";
string token = "your_token";

int intervalSeconds = 10;


using var client = new HttpClient();
client.DefaultRequestHeaders.UserAgent.Add(
    new ProductInfoHeaderValue("BuildMonitor", "1.0"));
client.DefaultRequestHeaders.Authorization =
    new AuthenticationHeaderValue("Bearer", token);

string lastState = "";
var lastState_tmp = "NO_BUILD";
string lastCommitSha = "";

new Thread(SetLedThread).Start(); 

while (true)
{
    try
    {
        lastState = await GetBuildState();        
    }
    catch (Exception ex)
    {
        Console.WriteLine("Error: " + ex.Message);
    }

    await Task.Delay(intervalSeconds * 1000);
}

async Task<string> GetLatestCommitSha()
{
    var url = $"https://api.github.com/repos/{owner}/{repo}/commits?per_page=1";

    var response = await client.GetAsync(url);
    var json = await response.Content.ReadAsStringAsync();

    using var doc = JsonDocument.Parse(json);

    var commits = doc.RootElement;

    if (commits.GetArrayLength() == 0)
        return "";

    return commits[0].GetProperty("sha").GetString();
}
async Task<string> GetBuildState()
{
    // 🔥 Always check commit first
    var latestSha = await GetLatestCommitSha();

    if (!string.IsNullOrEmpty(lastCommitSha) && latestSha != lastCommitSha)
    {
        lastCommitSha = latestSha;
        return "NEW_COMMIT";
    }

    lastCommitSha = latestSha;

    // Then check Actions
    var url = $"https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page=1";

    var response = await client.GetAsync(url);
    var json = await response.Content.ReadAsStringAsync();

    using var doc = JsonDocument.Parse(json);

    var runs = doc.RootElement.GetProperty("workflow_runs");

    if (runs.GetArrayLength() == 0)
        return "NO_BUILD";

    var run = runs[0];

    var status = run.GetProperty("status").GetString();
    var conclusion = run.GetProperty("conclusion").GetString();

    if (status == "queued" || status == "in_progress")
        return "BUILDING";

    if (status == "completed")
    {
        if (conclusion == "success")
            return "SUCCESS";
        else
            return "FAILED";
    }

    return "NO_BUILD";
}


void SetLedThread()
{
    var counter = 0;
    while (true)
    {
        if (lastState_tmp != lastState)
        {
            lastState_tmp = lastState;

            switch (lastState)
            {
                case "SUCCESS":
                    duelink.Engine.ExecuteCommand($"LEye(0,255,0)");
                    duelink.Engine.ExecuteCommand($"REye(0,255,0)");
                    duelink.Engine.ExecuteCommand($"Mouth({0},{0},{0})");
                    duelink.Engine.ExecuteCommand($"SetEar({0},{0})");
                    break;
                case "FAILED":
                    duelink.Engine.ExecuteCommand($"LEye(255,0,0)");
                    duelink.Engine.ExecuteCommand($"REye(255,0,0)");
                    duelink.Engine.ExecuteCommand($"Mouth({0},{0},{0})");
                    duelink.Engine.ExecuteCommand($"SetEar({0},{0})");

                    break;
                case "NO_BUILD":
                    duelink.Engine.ExecuteCommand($"LEye(0,0,255)");
                    duelink.Engine.ExecuteCommand($"REye(0,0,255)");
                    duelink.Engine.ExecuteCommand($"Mouth({0},{0},{0})");
                    duelink.Engine.ExecuteCommand($"SetEar({0},{0})");
                    break;

                case "NEW_COMMIT":

                    for (int i = 0; i < 10; i++)
                    {
                        var eye = i % 2 == 0 ? 50 : 0;
                        var mouth = i % 2 == 0 ? 0 : 50;
                        duelink.Engine.ExecuteCommand("freq(3,2000,50,0.5)");
                        duelink.Engine.ExecuteCommand($"LEye({eye},{eye},{eye})");
                        duelink.Engine.ExecuteCommand($"REye({eye},{eye},{eye})");
                        duelink.Engine.ExecuteCommand($"SetEar({mouth},{mouth})");
                        duelink.Engine.ExecuteCommand($"Mouth({mouth},{mouth},{mouth})");
                        Thread.Sleep(100);
                    }

                   
                    break;
            }
            
        }

        if (lastState == "BUILDING")
        {
            var eye = counter % 2 == 0 ? 50: 0;
            var mouth = counter % 2 == 0 ? 0 : 50;
            duelink.Engine.ExecuteCommand("freq(3,2000,50,0.5)");
            duelink.Engine.ExecuteCommand($"LEye({eye},{eye},{eye})");
            duelink.Engine.ExecuteCommand($"REye({eye},{eye},{eye})");
            duelink.Engine.ExecuteCommand($"Mouth({mouth},{mouth},{mouth})");
            
        }
        
        counter++;
        Thread.Sleep(50);
    }
}