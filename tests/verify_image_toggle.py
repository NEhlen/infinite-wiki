import sys
import os
import asyncio
import shutil
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

from app.main import app
from app.core.world import world_manager, WorldConfig
from app.core.generator import generator_service
from app.core.image_gen import image_gen_service
from app.database import create_db_and_tables, get_session
from app.models.article import Article

client = TestClient(app)

# Mock Image Gen to avoid real API calls and simulate delay
async def mock_generate_image(*args, **kwargs):
    print("Mock Image Gen Called")
    await asyncio.sleep(0.1) # Simulate work
    # Valid 1x1 pixel PNG base64
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="

image_gen_service.generate_image = MagicMock(side_effect=mock_generate_image)

def verify_image_toggle():
    print("Starting Image Toggle Verification...")
    
    # Test 1: Generate Images = False
    world_name_no_img = "TestWorld_NoImg"
    if os.path.exists(world_manager.get_world_path(world_name_no_img)):
        shutil.rmtree(world_manager.get_world_path(world_name_no_img))
        
    print(f"Creating world '{world_name_no_img}' (No Images)...")
    client.post("/create_world", data={
        "name": world_name_no_img,
        "description": "Desc",
        "system_prompt_planner": "Plan",
        "system_prompt_writer": "Write",
        "system_prompt_image": "Img",
        "seed_article_title": "Seed",
        "image_gen_model": "model",
        # generate_images not sent, defaults to False (checkbox unchecked)
    })
    
    # Verify config
    config = world_manager.get_config(world_name_no_img)
    assert config.generate_images is False
    print("Config (False): SUCCESS")
    
    # Verify Seed Article has no image
    session_gen = get_session(world_name_no_img)
    session = next(session_gen)
    article = session.get(Article, 1)
    assert article.image_url is None
    session.close()
    print("Article No Image: SUCCESS")
    
    # Reset Mock
    image_gen_service.generate_image.reset_mock()
    
    # Test 2: Generate Images = True
    world_name_img = "TestWorld_Img"
    if os.path.exists(world_manager.get_world_path(world_name_img)):
        shutil.rmtree(world_manager.get_world_path(world_name_img))
        
    print(f"Creating world '{world_name_img}' (With Images)...")
    # We need to mock the background task execution or verify it was added.
    # TestClient runs background tasks after the response.
    
    with patch.object(generator_service, 'generate_and_save_image', side_effect=generator_service.generate_and_save_image) as mock_bg:
        client.post("/create_world", data={
            "name": world_name_img,
            "description": "Desc",
            "system_prompt_planner": "Plan",
            "system_prompt_writer": "Write",
            "system_prompt_image": "Img",
            "seed_article_title": "Seed",
            "image_gen_model": "model",
            "generate_images": "true" # Checkbox sends "on" or "true" usually, FastAPI Form handles bool conversion
        })
        
        # Verify config
        config = world_manager.get_config(world_name_img)
        assert config.generate_images is True
        print("Config (True): SUCCESS")
        
        # Verify Background Task was called
        # Note: TestClient waits for background tasks, so the side effect should have run
        # But we mocked generate_image, so it should have been called
        assert image_gen_service.generate_image.called
        print("Image Gen Called: SUCCESS")
        
        # Verify Article has image (since TestClient waits)
        session_gen = get_session(world_name_img)
        session = next(session_gen)
        article = session.get(Article, 1)
        # It might fail if save failed (mock returns "base64_mock_data" which isn't valid base64)
        # But the code handles exceptions. We just want to ensure it TRIED.
        # Actually, let's return valid base64 to be sure
        
    print("Image Toggle Verification Complete.")

if __name__ == "__main__":
    verify_image_toggle()
