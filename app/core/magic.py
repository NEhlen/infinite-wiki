from pydantic import BaseModel, Field
from app.core.llm import llm_service
from app.core.world import WorldConfig
from app.config import get_settings

settings = get_settings()


class MagicConfigResponse(BaseModel):
    name: str = Field(
        description="A creative name for the world, directory safe (alphanumeric, hyphens, underscores)."
    )
    description: str = Field(description="A short description of the world.")
    system_prompt_planner: str = Field(
        description="The system prompt for the Planner LLM."
    )
    system_prompt_writer: str = Field(
        description="The system prompt for the Writer LLM."
    )
    system_prompt_image: str = Field(
        description="The system prompt for the Image Generation model."
    )
    generate_images: bool = Field(
        default=True,
        description="Whether to generate images for articles in this world.",
    )
    seed_article_title: str = Field(
        description="A catchy title for the first article to seed the wiki (e.g., 'The Great Cataclysm', 'The Founding of X')."
    )
    seed_article_description: str = Field(
        description="A short description/instruction for the seed article to guide its generation."
    )


class MagicService:
    async def generate_config(self, user_prompt: str) -> WorldConfig:
        system_prompt = """
        You are a world-building expert. Your goal is to translate a user's vague idea into a concrete configuration for an Infinite Wiki.
        
        Generate:
        1. A creative, directory-safe Name.
        2. A Description.
        3. Specialized System Prompts for:
           - Planner: Focus on the specific genre, tone, and rules of the world.
           - Writer: Focus on the writing style (e.g., academic, diary, propaganda, ensure that the writing style is written from within the world canonical context view).
           - Image: Focus on the visual style (e.g., photorealistic, oil painting, pixel art).
        4. A Seed Article Title: The most important foundational event, place, or concept to start the wiki.
        5. A Seed Article Description: A short paragraph describing what this first article should cover.
        """

        response = await llm_service.generate_json(
            user_prompt,
            schema=MagicConfigResponse,
            model=settings.LLM_MODEL,
            system_prompt=system_prompt,
        )

        data = MagicConfigResponse.model_validate(response)

        # We return a dict to include the seed title which isn't in WorldConfig
        return {
            "name": data.name,
            "description": data.description,
            "system_prompt_planner": data.system_prompt_planner,
            "system_prompt_writer": data.system_prompt_writer,
            "system_prompt_image": data.system_prompt_image,
            "llm_model": settings.LLM_MODEL,
            "image_gen_model": settings.IMAGE_GEN_MODEL,
            "generate_images": data.generate_images,
            "seed_article_title": data.seed_article_title,
            "seed_article_description": data.seed_article_description,
        }


magic_service = MagicService()
