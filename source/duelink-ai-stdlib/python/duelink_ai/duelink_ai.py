from .engine import Engine


class DuelinkAI:
    def __init__(self, key, jsonPath, duelink=None):
        self.engine = Engine(key, jsonPath, duelink)

    async def Run(self, prompt):
        return await self.engine.Run(prompt)