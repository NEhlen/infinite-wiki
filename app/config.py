from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Infinite Wiki"
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    
    # Model Config
    LLM_MODEL: str = "grok-4-fast-reasoning-latest"
    IMAGE_GEN_MODEL: str = "grok-2-image-latest"

    # Image Generation Config (defaults to OpenAI if not set)
    IMAGE_GEN_API_KEY: str | None = None
    IMAGE_GEN_BASE_URL: str | None = None
    
    # System Prompts
    SYSTEM_PROMPT_PLANNER: str = "You are a creative world-building assistant. Your goal is to outline consistent and interesting wiki articles."
    SYSTEM_PROMPT_WRITER: str = "You are an encyclopedic writer. Write detailed, dry, but descriptive wiki articles based on the provided outline."
    SYSTEM_PROMPT_IMAGE: str = "You are an expert art director. Create detailed visual descriptions for sci-fi concept art."

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
