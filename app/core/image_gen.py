from openai import AsyncOpenAI
from app.config import get_settings
from app.core.llm import llm_service

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

    async def generate_image(self, prompt: str, model: str = None, response_format: str = "url") -> str:
        model = model or settings.IMAGE_GEN_MODEL
        try:
            response = await self.client.images.generate(
                model=model,
                prompt=prompt,
                n=1,
                response_format="b64_json" if response_format == "b64_json" else "url"
            )
            
            if response_format == "b64_json":
                return response.data[0].b64_json
            else:
                return response.data[0].url
        except Exception as e:
            print(f"Image generation failed: {e}")
            return "https://via.placeholder.com/1024x1024?text=Image+Generation+Failed"

    
    def optimize_image_prompt(self, image_prompt: str, context: str, model: str = None) -> str:
        model = model or settings.LLM_MODEL

        prompt = f"""
        Optimize the following image prompt for better results:
        
        Original Prompt: {image_prompt}
        
        Context:
        {context}
        
        Goal: Create a concise, high-quality image prompt that will generate a visually appealing and informative image.
        If there is a contradiction between the original prompt and the context, use the context to resolve the contradiction.

        Return only the optimized prompt, do not include any additional text.
        """
        optimization_system_prompt = "You are an expert art director."
        optimized_prompt = llm_service.generate_text(prompt, model=model, system_prompt=optimization_system_prompt)
        return optimized_prompt

image_gen_service = ImageGenService()
