from openai import AsyncOpenAI
from app.config import get_settings

settings = get_settings()

class ImageGenService:
    def __init__(self):
        # Use specific image gen config if available, otherwise fall back to main OpenAI config
        api_key = settings.IMAGE_GEN_API_KEY or settings.OPENAI_API_KEY
        base_url = settings.IMAGE_GEN_BASE_URL or settings.OPENAI_BASE_URL
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )

    async def generate_image(self, prompt: str, model: str = None) -> str:
        model = model or settings.IMAGE_GEN_MODEL
        try:
            response = await self.client.images.generate(
                model=model,
                prompt=prompt,
                n=1,
                # size="1024x1024"
            )
            return response.data[0].url
        except Exception as e:
            print(f"Image generation failed: {e}")
            return None

image_gen_service = ImageGenService()
