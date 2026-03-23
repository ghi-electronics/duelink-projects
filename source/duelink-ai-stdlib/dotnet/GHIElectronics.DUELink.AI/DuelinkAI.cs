using System.Collections.Generic;
using System.Threading.Tasks;

namespace GHIElectronics.DUELink.AI
{
    public class DuelinkAI
    {
        private readonly Engine engine;

        public DuelinkAI(string key, string jsonPath, DUELinkController duelink = null)
        {
            engine = new Engine(key, jsonPath, duelink);
        }

        public string[] KnownKeywords {
            get { return engine.KnownKeywords; }
            set { engine.KnownKeywords = value; }
        }

        public Dictionary<string, string[]> ToolDictionaryMap
        {
            get => engine.ToolDictionaryMap;
            set => engine.ToolDictionaryMap = value;
        }

        public string StrictRules
        {
            get { return engine.StrictRules; }
            set { engine.StrictRules = value; }

        }

        public bool Verbose
        {
            get { return engine.Verbose; }
            set { engine.Verbose = value; }
        } 

        public Task<string[]> Run(string prompt)
        {
            return engine.Run(prompt);
        }
    }
}
