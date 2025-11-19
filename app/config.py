from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Literal
from functools import lru_cache
import keyring

# Define allowed providers
ProviderType = Literal["openai", "xai", "gemini", "custom", "auto"]

class Settings(BaseSettings):
    APP_NAME: str = "Infinite Wiki"
    
    # --- Provider Configuration ---
    # "auto" checks keyring priorities (OpenAI -> xAI -> Gemini)
    AI_PROVIDER: ProviderType = "auto"
    
    # We initialize these as None so the validator can populate them dynamically
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str | None = None
    
    # --- Model Config ---
    # We leave these as None by default to allow the provider to set smart defaults.
    # If you set LLM_MODEL in your .env, that value will take priority.
    LLM_MODEL: str | None = None
    IMAGE_GEN_MODEL: str | None = None

    # --- Image Generation Config ---
    # Defaults to using the main OPENAI_API_KEY if not explicitly set
    IMAGE_GEN_API_KEY: str | None = None
    IMAGE_GEN_BASE_URL: str | None = None
    
    # --- System Prompts ---
    SYSTEM_PROMPT_PLANNER: str = "You are a creative world-building assistant. Your goal is to outline consistent and interesting wiki articles."
    SYSTEM_PROMPT_WRITER: str = "You are an encyclopedic writer. Write detailed, dry, but descriptive wiki articles based on the provided outline."
    SYSTEM_PROMPT_IMAGE: str = "You are an expert art director. Create detailed visual descriptions for sci-fi concept art."

    class Config:
        env_file = ".env"
        # This allows extra fields in .env without throwing errors
        extra = "ignore" 

    @model_validator(mode='after')
    def configure_provider_settings(self):
        """
        Configures Keys, URLs, and Default Models based on the selected AI_PROVIDER.
        """
        # 1. Lazy load keys from system keyring
        key_openai = keyring.get_password("openai", "OPENAI_API_KEY")
        key_xai    = keyring.get_password("xai", "XAI_API_KEY")
        key_gemini = keyring.get_password("google", "GEMINI_API_KEY")

        # 2. Auto-detect provider if set to 'auto'
        if self.AI_PROVIDER == "auto":
            if self.OPENAI_API_KEY: # Env var takes priority
                self.AI_PROVIDER = "openai"
            elif key_openai:
                self.AI_PROVIDER = "openai"
            elif key_xai:
                self.AI_PROVIDER = "xai"
            elif key_gemini:
                self.AI_PROVIDER = "gemini"
            else:
                self.AI_PROVIDER = "openai" # Fallback

        # 3. Apply Provider Settings
        match self.AI_PROVIDER:
            case "openai":
                self.OPENAI_API_KEY = self.OPENAI_API_KEY or key_openai
                
                if not self.OPENAI_BASE_URL:
                    self.OPENAI_BASE_URL = "https://api.openai.com/v1"
                
                # Set default models if not provided in .env
                if not self.LLM_MODEL:
                    self.LLM_MODEL = "gpt-5-mini-latest"
                if not self.IMAGE_GEN_MODEL:
                    self.IMAGE_GEN_MODEL = "gpt-image-1-mini"

            case "xai":
                self.OPENAI_API_KEY = self.OPENAI_API_KEY or key_xai
                
                if not self.OPENAI_BASE_URL:
                    self.OPENAI_BASE_URL = "https://api.x.ai/v1"
                
                if not self.LLM_MODEL:
                    self.LLM_MODEL = "grok-4-fast-reasoning-latest"
                if not self.IMAGE_GEN_MODEL:
                    self.IMAGE_GEN_MODEL = "grok-2-image-latest"

            case "gemini":
                self.OPENAI_API_KEY = self.OPENAI_API_KEY or key_gemini
                
                if not self.OPENAI_BASE_URL:
                    # Google's OpenAI-compatible endpoint
                    self.OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
                
                if not self.LLM_MODEL:
                    self.LLM_MODEL = "gemini-2.5-flash-latest"
                if not self.IMAGE_GEN_MODEL:
                    # Gemini doesn't fully support image gen via the OpenAI-compat endpoint yet
                    # falling back or using a placeholder
                    self.IMAGE_GEN_MODEL = "gemini-2.5-flash-latest" 

            case "custom":
                # For custom (local LLMs), we assume user sets URL/Key in .env
                if not self.LLM_MODEL:
                    self.LLM_MODEL = "local-model" 

        # 4. Final Fallback for Image Gen Key
        # If no specific image key is provided, reuse the text generation key
        if not self.IMAGE_GEN_API_KEY:
            self.IMAGE_GEN_API_KEY = self.OPENAI_API_KEY
        
        if not self.IMAGE_GEN_BASE_URL:
            self.IMAGE_GEN_BASE_URL = self.OPENAI_BASE_URL

        return self

@lru_cache()
def get_settings() -> Settings:
    return Settings()