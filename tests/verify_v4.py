import sys
import os
import asyncio
import shutil
import base64

# Add project root to path
sys.path.append(os.getcwd())

from app.core.world import world_manager, WorldConfig
from app.database import create_db_and_tables, get_session
from app.core.generator import generator_service
from app.models.article import Article

# Mock LLM and Image Gen
from unittest.mock import MagicMock
from app.core.llm import llm_service
from app.core.image_gen import image_gen_service

async def mock_generate_json(*args, **kwargs):
    return {
        "summary": "A test summary for V4.",
        "outline": ["Intro"],
        "entities": [],
        "image_prompt": "A local image test",
        "image_caption": "Local image caption",
        "year": "2025",
        "timeline_event": "Local storage implemented."
    }

async def mock_generate_text(*args, **kwargs):
    return "Content for V4 test."

async def mock_generate_image(prompt, model=None, response_format="url"):
    if response_format == "b64_json":
        # Return a 1x1 pixel transparent PNG base64
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    return "http://example.com/fail.png"

llm_service.generate_json = MagicMock(side_effect=mock_generate_json)
llm_service.generate_text = MagicMock(side_effect=mock_generate_text)
image_gen_service.generate_image = MagicMock(side_effect=mock_generate_image)

async def verify_v4():
    print("Starting V4 Verification...")
    
    world_name = "TestWorld_V4"
    
    # 1. Clean up
    world_path = world_manager.get_world_path(world_name)
    if os.path.exists(world_path):
        shutil.rmtree(world_path)
        
    # 2. Create World
    print(f"Creating world '{world_name}'...")
    config = WorldConfig(
        name=world_name,
        description="A test world for V4.",
        system_prompt_planner="P",
        system_prompt_writer="W",
        system_prompt_image="I"
    )
    world_manager.create_world(config)
    create_db_and_tables(world_name)
    
    # 3. Generate Article with Image
    print("Generating article 'Local Image Test'...")
    session_gen = get_session(world_name)
    session = next(session_gen)
    
    try:
        article = await generator_service.generate_article(world_name, "Local Image Test", session)
        
        # 4. Verify Image URL and File
        print(f"Image URL: {article.image_url}")
        
        expected_url = f"/world/{world_name}/images/Local_Image_Test.png"
        if article.image_url == expected_url:
            print("Image URL Format: SUCCESS")
        else:
            print(f"Image URL Format: FAILED (Got {article.image_url})")
            
        # Check file existence
        images_path = world_manager.get_images_path(world_name)
        file_path = os.path.join(images_path, "Local_Image_Test.png")
        if os.path.exists(file_path):
            print("Image File Saved: SUCCESS")
        else:
            print("Image File Saved: FAILED")
            
    finally:
        session.close()
        
    print("V4 Verification Complete.")

if __name__ == "__main__":
    asyncio.run(verify_v4())
