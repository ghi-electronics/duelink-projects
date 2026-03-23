//In this sample:

//Read events from the Minetest game
//Transfer events to the DUELink smart LED

using GHIElectronics.DUELink;
using System;
using System.Drawing;
using System.Text;

var availablePort = DUELinkController.GetConnectionPort();
var duelink = new DUELinkController(availablePort);

// The output file is saved in bin folder. We just need to read from there.
// File name "gamepulse.txt" is defined in init.lua
const string path = @"C:\Minetest\luanti-5.15.1-win64\bin\gamepulse.txt";

int lastPunch = 0;
int lasthp = 0;
void InitWS2811(int width, int heigh)
{
    duelink.Engine.ExecuteCommand($"dim a1[] = {{14,{width},{heigh},1}}");
    duelink.Engine.ExecuteCommand($"GfxCfg(3, a1, {width},{heigh}, 1)");

    SetColor(0x000005);
}

void SetColor(uint color)
{
    duelink.Engine.ExecuteCommand($"Clear({color}):show()");
}

void DrawHp(int hp)
{
    duelink.Engine.ExecuteCommand($"Clear(0):Text(\"{hp.ToString()}\",0xFF,0,0):show()");
}

InitWS2811(16, 16);
while (true)
{
    if (File.Exists(path))
    {
        try
        {
            var text = File.ReadAllText(path);
            var parts = text.Trim().Split(',');
            int punch = 0;
            int hp = 0;

            foreach (var p in parts)
            {
                var kv = p.Split(':');
                if (kv.Length != 2) continue;

                var key = kv[0].Trim();
                var value = kv[1].Trim();

                switch (key)
                {
                  
                    case "PUNCH":
                        int.TryParse(value, out punch);
                        break;

                    case "HP":
                        int.TryParse(value, out hp);
                        break;
                }
            }

            if (lastPunch != punch || lasthp != hp)
            {
                lastPunch = punch;
                lasthp = hp;
                Console.WriteLine($"Punch:{punch} | HP:{hp} ");
                if (punch==1)
                {
                    SetColor(0xFF0000u);
                }
                else
                {
                    DrawHp(hp);
                }
                    
            }
        }
        catch
        {
            Console.WriteLine("sync problem, ignored");
        }
    }

    await Task.Delay(50); // faster + responsive
}