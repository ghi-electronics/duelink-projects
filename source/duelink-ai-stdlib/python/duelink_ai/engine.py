import os
import json
import aiohttp


class Engine:
    def __init__(self, key, jsonPath, duelink):
        self.apiKey = key
        self.lastPin = 1
        self.duelink = duelink

        if os.path.exists(jsonPath):
            self.jsonFiles = [
                os.path.join(jsonPath, f)
                for f in os.listdir(jsonPath)
                if f.endswith(".json")
            ]
        else:
            self.jsonFiles = []

        self.knownKeywords = [
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
            "pid","product id","firmware",
            "reset","erase"
        ]

        self.toolDictionaryMap = {
            "statusled": ["led", "blink", "flash", "pin", "high", "low", "on", "off"],
            "digital": ["digital", "pin", "high", "low", "on", "off"],
            "analog": ["analog", "volt", "voltage", "adc", "vcc"],
            "sound": ["beep", "sound", "buzzer", "tone", "play", "hz", "khz", "mhz"],
            "frequency": ["frequency", "pwm", "duty", "cyle", "dutycyle", "hz", "khz", "mhz"],
            "system": ["version", "info", "reset", "device", "pid", "product id", "firmware"],
            "i2c": ["i2c", "two wire", "bus"],
            "spi": ["spi"],
            "uart": ["uart", "serial", "tx", "rx"],
            "deviceaddressing": ["sel", "address", "device address"],
            "filesystem": ["file", "fs", "read file", "write file", "directory"],
            "graphics": ["graphics", "draw", "display", "pixel", "text", "circle", "screen", "show", "clear", "fill", "line", "color", "image"],
            "math": ["sin", "cos", "tan", "sqrt", "random"],
            "converter": ["convert", "hex", "format", "scale", "base64"],
            "interrupt": ["interrupt", "irq", "trigger", "callback"],
            "downlinkcontrol": ["downlink"],
            "button": ["button", "press"],
            "distance": ["distance", "ultrasonic", "trigger", "echo"],
            "servomotor": ["servo", "motor angle", "degree"],
            "temperature": ["temperature", "temp", "dht"],
            "humidity": ["humidity"],
            "print": ["print", "println"]
        }

        self.strictRules = (
            "STRICT RULES:"
            "\n- ALWAYS call a function"
            "\n- NEVER return text"
            "\n- Use ONLY provided functions"
            "\n- DO NOT invent names"
            "\n- Follow parameters EXACTLY"
            "\n- Arrays must be [ ... ]"
            "\n- 1 second = 1000"
            "\n- on=1, off=0"
            "\n- Use milliseconds (1 second = 1000)"
            "\n- If user says 'on' → value=1"
            "\n- If user says 'off' → value=0"
            "\n- Follow parameter meaning strictly"
            "\n- Use enums when available"
        )

        self.Verbose = True

    # =========================
    async def Run(self, prompt):
        prompt = self.Normalize(prompt)

        topics = self.GetSupportedTopics(self.jsonFiles)

        if (not self.IsHelpRequest(prompt)) and self.IsUnknownRequest(prompt, self.jsonFiles):
            return [f"This request is not supported. \nEnhance the JSON files, KnownKeywords, and ToolDictionaryMap properties to improve intelligence and accuracy"]

        toolsFile = self.SelectTool(prompt, self.jsonFiles)
        tools = open(toolsFile, "r", encoding="utf-8").read()

        if self.IsHelpRequest(prompt):
            help_text = await self.CallOpenAIHelp(prompt, tools)
            return [help_text]

        response = await self.CallOpenAI(prompt, tools)
        cmds = self.ParseTools(response)

        result = []
        for cmd in cmds:
            result.append(self.Execute(cmd))

        return result

    # =========================
    def Normalize(self, input):
        input = input.lower()
        input = input.replace("one second", "1000 ms")
        input = input.replace("1 second", "1000 ms")
        input = input.replace("half second", "500 ms")
        input = input.replace("turn on", "set high")
        input = input.replace("turn off", "set low")
        return input

    def IsHelpRequest(self, prompt):
        prompt = prompt.lower()
        return ("help" in prompt or
                "what is" in prompt or
                "explain" in prompt or
                "how to use" in prompt)

    def GetSupportedTopics(self, files):
        topics = list(set([
            os.path.splitext(os.path.basename(f))[0].lower()
            for f in files
        ]))
        return ", ".join(topics)

    def IsUnknownRequest(self, prompt, files):
        prompt = prompt.lower()

        for f in files:
            name = os.path.splitext(os.path.basename(f))[0].lower()
            if name in prompt:
                return False

        if any(k in prompt for k in self.knownKeywords):
            return False

        return True

    # =========================
    def BuildHelpPrompt(self, prompt, toolJson):
        return f"""
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
"""

    async def CallOpenAIHelp(self, prompt, toolsJson):
        headers = {
            "Authorization": f"Bearer {self.apiKey}",
            "Content-Type": "application/json"
        }

        request = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a friendly DUELink teacher helping beginners understand hardware APIs."},
                {"role": "user", "content": self.BuildHelpPrompt(prompt, toolsJson)}
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=request) as res:
                data = await res.json()
                return data["choices"][0]["message"]["content"]

    # =========================
    def SelectTool(self, prompt, files):
        prompt = prompt.lower()
        candidates = []

        for k, v in self.toolDictionaryMap.items():
            if any(x in prompt for x in v):
                candidates.append(k)

        if len(candidates) == 0:
            return self.FindFile(files, "digital") or files[0]

        if len(candidates) == 1:
            return self.FindFile(files, candidates[0])

        scores = {}

        for c in candidates:
            my = self.toolDictionaryMap[c]
            others = [x for k in candidates if k != c for x in self.toolDictionaryMap[k]]

            score = sum(1 for k in my if k in prompt and k not in others)
            scores[c] = score

        maxScore = max(scores.values())
        best = [k for k, v in scores.items() if v == maxScore]

        if len(best) == 1:
            return self.FindFile(files, best[0])

        bestMatch = None
        bestIndex = 999999

        for c in best:
            for k in self.toolDictionaryMap[c]:
                idx = prompt.find(k)
                if idx >= 0 and idx < bestIndex:
                    bestIndex = idx
                    bestMatch = c

        if bestMatch:
            return self.FindFile(files, bestMatch)

        return self.FindFile(files, "digital") or files[0]

    def FindFile(self, files, keyword):
        keyword = keyword.lower()

        for f in files:
            name = os.path.splitext(os.path.basename(f))[0].lower()
            if name == keyword:
                return f

        for f in files:
            name = os.path.splitext(os.path.basename(f))[0].lower()
            if keyword in name:
                return f

        return None

    # =========================
    async def CallOpenAI(self, prompt, toolsJson):
        headers = {
            "Authorization": f"Bearer {self.apiKey}",
            "Content-Type": "application/json"
        }

        tools = json.loads(toolsJson)["tools"]

        request = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a DUELink hardware assistant.\n\nConvert user request into function calls.\n\n" + self.strictRules},
                {"role": "user", "content": prompt}
            ],
            "tools": tools,
            "tool_choice": "required"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=request) as res:
                return await res.text()

    # =========================
    def ParseTools(self, json_str):
        doc = json.loads(json_str)

        if "error" in doc:
            print("OpenAI Error:", doc["error"]["message"])
            return []

        if "choices" not in doc:
            print("Invalid response:", json_str)
            return []

        message = doc["choices"][0].get("message", {})

        if "tool_calls" not in message:
            print("No tool call:", message.get("content"))
            return []

        result = []

        for t in message["tool_calls"]:
            name = t["function"]["name"]
            args = json.loads(t["function"]["arguments"])
            result.append((name, args))

        return result

    # =========================
    def Execute(self, cmd):
        name, args = cmd

        command = name + "("

        if isinstance(args, dict):
            values = []

            for k in args:
                val = self.FormatValue(args[k])

                if k == "pin":
                    try:
                        self.lastPin = int(val)
                    except:
                        pass

                values.append(val)

            command += ",".join(values)

        command += ")"

        self.Log("SEND: " + command)

        if self.duelink:
            ret = self.duelink.Engine.ExecuteCommandRaw(command)

            if ret:
                self.Log("RETURN: " + ret)

            return ret

        return ""

    # =========================
    def FormatValue(self, val):
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, str):
            return f'"{val}"'
        if isinstance(val, list):
            return "[" + ",".join(str(x) for x in val) + "]"
        if isinstance(val, bool):
            return "1" if val else "0"
        return str(val)

    # =========================
    def Log(self, log):
        if self.Verbose:
            print(log)