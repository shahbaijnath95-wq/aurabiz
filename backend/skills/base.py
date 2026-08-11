from typing import Optional


class Skill:
    name: str = "base"
    description: str = "Base skill"
    capabilities: list[str] = []

    async def execute(self, context: dict) -> dict:
        return {"skill": self.name, "status": "executed"}

    def get_capabilities(self) -> list[str]:
        return self.capabilities

    def validate_input(self, context: dict) -> bool:
        return True

    def format_response(self, result: str) -> str:
        return result
