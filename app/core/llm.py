from openai import AsyncOpenAI
from app.config import get_settings
from pydantic import BaseModel

settings = get_settings()

class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )

    async def generate_text(self, prompt: str, model: str = "grok-4-fast-reasoning-latest", system_prompt: str = "You are a helpful assistant.") -> str:
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    async def generate_json(self, prompt: str, schema: BaseModel, model: str = "grok-4-fast-reasoning-latest", system_prompt: str = "You are a helpful assistant.") -> str:
        response = await self.client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format=schema,
        )
        return response.choices[0].message.parsed

llm_service = LLMService()
