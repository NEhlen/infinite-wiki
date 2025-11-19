import sys
import os
import asyncio
import shutil
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from app.core.world import world_manager, WorldConfig
from app.core.generator import generator_service
from app.core.llm import llm_service
from app.core.image_gen import image_gen_service
from app.database import create_db_and_tables, get_session

# Mock LLM and Image Gen to capture arguments
async def mock_generate_json(*args, **kwargs):
    print(f"LLM JSON Call - Model: {kwargs.get('model')}, System Prompt: {kwargs.get('system_prompt')}")
    return {
        "summary": "Test Summary",
        "outline": ["Intro", "Body"],
        "entities": [],
        "image_prompt": "Test Image",
        "image_caption": "Test Caption",
        "year": 2025,
        "timeline_event": "Test Event"
    }

async def mock_generate_text(*args, **kwargs):
    print(f"LLM Text Call - Model: {kwargs.get('model')}, System Prompt: {kwargs.get('system_prompt')}")
    return "Test Content"

async def mock_generate_image(*args, **kwargs):
    print(f"Image Gen Call - Model: {kwargs.get('model')}")
    return "base64_mock_data"

llm_service.generate_json = MagicMock(side_effect=mock_generate_json)
llm_service.generate_text = MagicMock(side_effect=mock_generate_text)
image_gen_service.generate_image = MagicMock(side_effect=mock_generate_image)

def verify_config_usage():
    print("Starting Config Verification...")
    
    world_name = "TestWorld_Config"
    
    # 1. Clean up
    world_path = world_manager.get_world_path(world_name)
    if os.path.exists(world_path):
        shutil.rmtree(world_path)
        
    # 2. Create World with Custom Config
    print(f"Creating world '{world_name}' with custom config...")
    config = WorldConfig(
        name=world_name,
        description="A test world.",
        system_prompt_planner="CUSTOM_PLANNER_PROMPT",
        system_prompt_writer="CUSTOM_WRITER_PROMPT",
        system_prompt_image="CUSTOM_IMAGE_PROMPT",
        llm_model="custom-llm-model",
        image_gen_model="custom-image-model"
    )
    world_manager.create_world(config)
    create_db_and_tables(world_name)
    
    # 3. Trigger Generation
    print("Triggering Article Generation...")
    session_gen = get_session(world_name)
    session = next(session_gen)
    
    asyncio.run(generator_service.generate_article(world_name, "Test Article", session))
    
    session.close()
    
    # 4. Verify Calls
    print("\nVerifying Calls:")
    
    # Check Planner Call
    calls_json = llm_service.generate_json.call_args_list
    planner_call = calls_json[0]
    assert planner_call.kwargs['model'] == "custom-llm-model"
    assert planner_call.kwargs['system_prompt'] == "CUSTOM_PLANNER_PROMPT"
    print("Planner Config: SUCCESS")
    
    # Check Writer Call
    calls_text = llm_service.generate_text.call_args_list
    writer_call = calls_text[0]
    assert writer_call.kwargs['model'] == "custom-llm-model"
    assert writer_call.kwargs['system_prompt'] == "CUSTOM_WRITER_PROMPT"
    print("Writer Config: SUCCESS")
    
    # Check Image Gen Call
    calls_image = image_gen_service.generate_image.call_args_list
    image_call = calls_image[0]
    assert image_call.kwargs['model'] == "custom-image-model"
    print("Image Gen Config: SUCCESS")
    
    print("\nConfig Verification Complete.")

if __name__ == "__main__":
    verify_config_usage()
