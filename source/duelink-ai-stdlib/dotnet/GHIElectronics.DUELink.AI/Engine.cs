using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Reflection.Metadata.Ecma335;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace GHIElectronics.DUELink.AI
{
    internal class Engine
    {
        private string apiKey;
        private int lastPin = 1;
        private string[] jsonFiles;
        private DUELinkController duelink;

        public Engine(string key, string jsonPath, DUELinkController duelink)
        {
            apiKey = key;

            var dir = jsonPath;
            if (Directory.Exists(dir))
                jsonFiles = Directory.GetFiles(dir, "*.json");
            else
                jsonFiles = Array.Empty<string>();

            this.duelink = duelink; 


        }

        public async Task<string[]> Run(string prompt)
        {
            prompt = Normalize(prompt);

            var topics = GetSupportedTopics(jsonFiles);

            if (!IsHelpRequest(prompt) && IsUnknownRequest(prompt, jsonFiles))
            {
                return new[] { $"This request is not supported. \nEnhance the JSON files, KnownKeywords, and ToolDictionaryMap properties to improve intelligence and accuracy" };
            }

            var toolsFile = SelectTool(prompt, jsonFiles);
            var tools = File.ReadAllText(toolsFile);

            if (IsHelpRequest(prompt))
            {
                var help = await CallOpenAIHelp(prompt, tools);
                return new[] { help };
            }

            var response = await CallOpenAI(prompt, tools);
            var cmds = ParseTools(response);

            var list = new List<string>();

            foreach (var cmd in cmds)
            {
                list.Add(Execute(cmd));
            }

            return list.ToArray();
        }

        // =========================
        // NORMALIZE INPUT
        // =========================
        string Normalize(string input)
        {
            input = input.ToLower();

            // time conversion
            input = input.Replace("one second", "1000 ms");
            input = input.Replace("1 second", "1000 ms");
            input = input.Replace("half second", "500 ms");

            // intent mapping
            input = input.Replace("turn on", "set high");
            input = input.Replace("turn off", "set low");

            return input;
        }

        bool IsHelpRequest(string prompt)
        {
            prompt = prompt.ToLower();

            return prompt.Contains("help") ||
                   prompt.Contains("what is") ||
                   prompt.Contains("explain") ||
                   prompt.Contains("how to use");
        }



        string GetSupportedTopics(string[] files)
        {
            var topics = files
                .Select(f => Path.GetFileNameWithoutExtension(f).ToLower())
                .Distinct();

            return string.Join(", ", topics);
        }

        string[] knownKeywords = {
            "pin","led","blink","high","low",
            "analog","voltage",
            "beep","sound",
            "frequency","pwm",
            "info","version",
            "file","fs","read","write",
            "draw","display","text",
            "temperature","humidity",
            "servo","motor",
            "distance",
            "interrupt",
            "convert","scale","hex",
            "downlink","cmd",
            "pid", "product id","firmware",
            "reset", "erase"
        };

        public string[] KnownKeywords {
            get { return knownKeywords; }
            set { knownKeywords = value; }
        
        }

        bool IsUnknownRequest(string prompt, string[] files)
        {
            prompt = prompt.ToLower();

            foreach (var f in files)
            {
                var name = Path.GetFileNameWithoutExtension(f).ToLower();

                if (prompt.Contains(name))
                    return false;
            }

            if (knownKeywords.Any(k => prompt.Contains(k)))
                return false;

            return true;
        }        

        string BuildHelpPrompt(string prompt, string toolJson)
        {
            return $@"
User question: {prompt}

Here is the API definition:
{toolJson}

Explain this function for a beginner.

FORMAT STRICTLY:

1. Title
2. Simple explanation (very easy)
3. Parameters (bullet points)

4. Command (ready to run)
- Provide ONE real command line (like: statled(1000,1000,0))

5. Explanation of the command
- Explain what each value does in that example

6. What happens in real life

7. Suggest 1 thing to try next

Rules:
- Keep it simple
- Time must be milliseconds (1000 = 1 second)
- If duration=0 or count=0 means forever, explain it
- Command must be VALID and realistic
- DO NOT call function (this is explanation mode)
";
        }

        async Task<string> CallOpenAIHelp(string prompt, string toolsJson)
        {
            var http = new HttpClient();
            http.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");

            var request = new
            {
                model = "gpt-4o-mini",
                messages = new object[]
                {
            new {
                role = "system",
                content = "You are a friendly DUELink teacher helping beginners understand hardware APIs."
            },
            new {
                role = "user",
                content = BuildHelpPrompt(prompt, toolsJson)
            }
                }
            };

            var content = new StringContent(JsonSerializer.Serialize(request), Encoding.UTF8, "application/json");

            var res = await http.PostAsync("https://api.openai.com/v1/chat/completions", content);
            var json = await res.Content.ReadAsStringAsync();

            using var doc = JsonDocument.Parse(json);

            return doc.RootElement
                .GetProperty("choices")[0]
                .GetProperty("message")
                .GetProperty("content")
                .GetString();
        }

        // =========================
        // SELECT TOOL
        // =========================

        Dictionary<string, string[]> toolDictionaryMap = new Dictionary<string, string[]>
        {
            ["statusled"] = new[] { "led", "blink", "flash", "pin", "high", "low", "on", "off" },
            ["digital"] = new[] { "digital", "pin", "high", "low", "on", "off" },
            ["analog"] = new[] { "analog", "volt", "voltage", "adc", "vcc" },
            ["sound"] = new[] { "beep", "sound", "buzzer", "tone", "play", "hz", "khz", "mhz" },
            ["frequency"] = new[] { "frequency", "pwm", "duty", "cyle", "dutycyle", "hz", "khz", "mhz" },
            ["system"] = new[] { "version", "info", "reset", "device", "pid", "product id", "firmware" },
            ["i2c"] = new[] { "i2c", "two wire", "bus" },
            ["spi"] = new[] { "spi" },
            ["uart"] = new[] { "uart", "serial", "tx", "rx" },
            ["deviceaddressing"] = new[] { "sel", "address", "device address" },
            ["filesystem"] = new[] { "file", "fs", "read file", "write file", "directory" },
            ["graphics"] = new[] { "graphics", "draw", "display", "pixel", "text", "circle", "screen", "show", "clear", "fill", "line", "color", "image" },
            ["math"] = new[] { "sin", "cos", "tan", "sqrt", "random" },
            ["converter"] = new[] { "convert", "hex", "format", "scale", "base64" },
            ["interrupt"] = new[] { "interrupt", "irq", "trigger", "callback" },
            ["downlinkcontrol"] = new[] { "downlink" },
            ["button"] = new[] { "button", "press" },

            ["distance"] = new[] { "distance", "ultrasonic", "trigger", "echo" },

            ["servomotor"] = new[] { "servo", "motor angle", "degree" },
            ["temperature"] = new[] { "temperature", "temp", "dht" },
            ["humidity"] = new[] { "humidity" },
            ["print"] = new[] { "print", "println" }
        };

        public Dictionary<string, string[]> ToolDictionaryMap {  
            get => toolDictionaryMap;
            set => toolDictionaryMap = value; 
        }
        string SelectTool(string prompt, string[] files)
        {
            prompt = prompt.ToLower();

            var map = toolDictionaryMap;

            // ===== STEP 1: find candidates =====
            var candidates = new List<string>();

            foreach (var kv in map)
            {
                if (kv.Value.Any(k => prompt.Contains(k)))
                    candidates.Add(kv.Key);
            }

            if (candidates.Count == 0)
                return FindFile(files, "digital") ?? files[0];

            if (candidates.Count == 1)
                return FindFile(files, candidates[0]);

            // ===== STEP 2: unique keyword scoring =====
            var scores = new Dictionary<string, int>();

            foreach (var c in candidates)
            {
                var myKeywords = map[c];
                var others = candidates.Where(x => x != c).SelectMany(x => map[x]).ToList();

                int uniqueScore = myKeywords
                    .Where(k => prompt.Contains(k) && !others.Contains(k))
                    .Count();

                scores[c] = uniqueScore;
            }

            int maxScore = scores.Values.Max();

            var best = scores.Where(x => x.Value == maxScore).Select(x => x.Key).ToList();

            if (best.Count == 1)
                return FindFile(files, best[0]);

            // ===== STEP 3: earliest keyword wins =====
            string bestMatch = null;
            int bestIndex = int.MaxValue;

            foreach (var c in best)
            {
                foreach (var k in map[c])
                {
                    int idx = prompt.IndexOf(k);
                    if (idx >= 0 && idx < bestIndex)
                    {
                        bestIndex = idx;
                        bestMatch = c;
                    }
                }
            }

            if (bestMatch != null)
                return FindFile(files, bestMatch);

            return FindFile(files, "digital") ?? files[0];
        }

        string FindFile(string[] files, string keyword)
        {
            keyword = keyword.ToLower();

            // 1Exact match FIRST
            var exact = files.FirstOrDefault(f =>
                Path.GetFileNameWithoutExtension(f)
                    .Equals(keyword, StringComparison.OrdinalIgnoreCase));

            if (exact != null)
                return exact;

            // Fallback: contains
            return files.FirstOrDefault(f =>
                Path.GetFileNameWithoutExtension(f)
                    .ToLower()
                    .Contains(keyword));
        }

        // =========================
        // CALL OPENAI
        // =========================

        string strictRules = "STRICT RULES:" +
            "\n- ALWAYS call a function" +
            "\n- NEVER return text" +
            "\n- Use ONLY provided functions" +
            "\n- DO NOT invent names" +
            "\n- Follow parameters EXACTLY" +
            "\n- Arrays must be [ ... ]" +
            "\n- 1 second = 1000" +
            "\n- on=1, off=0" +
            "\n- Use milliseconds (1 second = 1000)" +
            "\n- If user says 'on' → value=1" +
            "\n- If user says 'off' → value=0" +
            "\n- Follow parameter meaning strictly" +
            "\n- Use enums when available";
        public string StrictRules {  
            get { return strictRules; } 
            set { strictRules = value; }
        
        }
        async Task<string> CallOpenAI(string prompt, string toolsJson)
        {
            var http = new HttpClient();
            http.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");

            using var doc = JsonDocument.Parse(toolsJson);
            var _tools = doc.RootElement.GetProperty("tools").EnumerateArray().ToArray();

            var request = new
            {
                model = "gpt-4o-mini",
                messages = new object[]
                {
                new {
                    role = "system",
                    content = @"You are a DUELink hardware assistant.

Convert user request into function calls.

" + strictRules
                },
                new { role = "user", content = prompt }
                },
                tools = _tools,
                tool_choice = "required"
            };

            var content = new StringContent(JsonSerializer.Serialize(request), Encoding.UTF8, "application/json");

            var res = await http.PostAsync("https://api.openai.com/v1/chat/completions", content);
            return await res.Content.ReadAsStringAsync();
        }

        // =========================
        // PARSE MULTI TOOL
        // =========================
        (string name, JsonElement args)[] ParseTools(string json)
        {
            using var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;

            //  CHECK ERROR FIRST
            if (root.TryGetProperty("error", out var err))
            {
                Console.WriteLine(" OpenAI Error:");
                Console.WriteLine(err.GetProperty("message").GetString());
                return Array.Empty<(string, JsonElement)>();
            }

            //  CHECK choices
            if (!root.TryGetProperty("choices", out var choices))
            {
                Console.WriteLine(" Invalid response: no choices");
                Console.WriteLine(json);
                return Array.Empty<(string, JsonElement)>();
            }

            var choice0 = choices[0];

            if (!choice0.TryGetProperty("message", out var message))
            {
                Console.WriteLine(" Invalid response: no message");
                Console.WriteLine(json);
                return Array.Empty<(string, JsonElement)>();
            }

            //  CHECK tool_calls
            if (!message.TryGetProperty("tool_calls", out var toolCalls))
            {
                Console.WriteLine(" No tool call. AI said:");
                if (message.TryGetProperty("content", out var content))
                    Console.WriteLine(content.GetString());

                return Array.Empty<(string, JsonElement)>();
            }

            var list = new List<(string, JsonElement)>();

            foreach (var tool in toolCalls.EnumerateArray())
            {
                var name = tool.GetProperty("function").GetProperty("name").GetString();
                var argsString = tool.GetProperty("function").GetProperty("arguments").GetString();
                var args = JsonDocument.Parse(argsString).RootElement;

                list.Add((name, args));
            }

            return list.ToArray();
        }

        // =========================
        // EXECUTE COMMAND
        // =========================
        string Execute((string name, JsonElement args) cmd)
        {
            if (cmd.name == "print" || cmd.name == "println")
            {
                if (cmd.args.TryGetProperty("values", out var values))
                {
                    // if only 1 element
                    if (values.GetArrayLength() == 1)
                    {
                        var v = values[0];

                        // number → convert to string
                        if (v.ValueKind == JsonValueKind.Number)
                        {                            
                            Log($"SEND: {cmd.name}(\"{v}\")");
                        }

                        // string → keep as is
                        if (v.ValueKind == JsonValueKind.String)
                        {

                            Log($"SEND: {cmd.name}(\"{v.GetString()}\")");
                        }
                    }

                    // multiple elements → array
                    var arr = values.EnumerateArray().Select(x => x.ToString());

        
                    Log($"SEND: {cmd.name}([{string.Join(",", arr)}])");
                }                
            }

            string command = cmd.name + "(";

            if (cmd.args.ValueKind == JsonValueKind.Object)
            {
                var values = new List<string>();

                foreach (var p in cmd.args.EnumerateObject())
                {
                    string val = FormatValue(p.Value);

                    if (p.Name == "pin" && int.TryParse(val, out int pin))
                        lastPin = pin;

                    values.Add(val);
                }

                command += string.Join(",", values);
            }

            command += ")";

            //Log("SEND: " + command);
            if (duelink == null)
            {
                Log("SEND: " + command);
            }
            else
            {
                Log("SEND: " + command);
                var ret = duelink.Engine.ExecuteCommandRaw(command);

                if ( ret != null && ret.Length > 0)
                {
                    Log("RETURN: " + ret);
                }
                
                
                return ret;
            }

            // TODO: serial.WriteCommand(command);
            return "";
        }

        // =========================
        // FIX VALUE
        // =========================
        string FixValue(string v)
        {
            v = v.ToLower();

            if (v == "high" || v == "on") return "1";
            if (v == "low" || v == "off") return "0";

            return v;
        }

        string FormatValue(JsonElement val)
        {
            switch (val.ValueKind)
            {
                case JsonValueKind.Number:
                    return val.ToString();

                case JsonValueKind.String:
                    return $"\"{val.GetString()}\""; //  always quote

                case JsonValueKind.Array:
                    var items = val.EnumerateArray().Select(x => x.ToString());
                    return "[" + string.Join(",", items) + "]";

                case JsonValueKind.True:
                    return "1";

                case JsonValueKind.False:
                    return "0";

                default:
                    return val.ToString();
            }
        }

        public bool Verbose { get; set; } = true;
        void Log(string log) { 
            if (Verbose) Console.WriteLine(log);
            
        }    
    }
}
