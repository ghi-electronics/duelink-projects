using GHIElectronics.DUELink;
using System;
using System.Drawing;
using System.Net.Http;
using System.Text.Json;
using System.Xml.Serialization;

var availablePort = DUELinkController.GetConnectionPort();
var duelink = new DUELinkController(availablePort);

void SetLed(Color color)
{
    duelink.Engine.ExecuteCommand($"SetLed(0,{color.ToArgb()})");
    duelink.Engine.ExecuteCommand($"SetLed(1,{color.ToArgb()})");
    duelink.Engine.ExecuteCommand($"SetLed(2,{color.ToArgb()})");
}

Console.Write("Enter stock symbol (e.g. AAPL): ");
var symbol = Console.ReadLine()?.ToUpper();

var apiKey = "YOUR_API_KEY";
decimal? lastPrice = null;

using var client = new HttpClient();

SetLed(Color.White);

while (true)
{
    try
    {
        var url = $"https://finnhub.io/api/v1/quote?symbol={symbol}&token={apiKey}";
        var json = await client.GetStringAsync(url);

        using var doc = JsonDocument.Parse(json);
        var currentPrice = doc.RootElement.GetProperty("c").GetDecimal();

        if (lastPrice != null)
        {
            if (currentPrice > lastPrice)
            {
                SetLed(Color.Green);
                Console.WriteLine($"{DateTime.Now}: UP ({currentPrice})");
            }

            else if (currentPrice < lastPrice)
            {
                SetLed(Color.Red);
                Console.WriteLine($"{DateTime.Now}: DOWN ({currentPrice})");
            }

            else
            {
                Console.WriteLine($"{DateTime.Now}: NO CHANGE ({currentPrice})");
            }
        }
        else
        {
            Console.WriteLine($"{DateTime.Now}: Initial Price = {currentPrice}");
        }

        lastPrice = currentPrice;
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Error: {ex.Message}");
    }

    await Task.Delay(5000);
}