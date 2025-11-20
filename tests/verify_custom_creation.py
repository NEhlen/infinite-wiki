import sys
import os
import asyncio
import shutil
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.getcwd())

from app.core.world import world_manager, WorldConfig
from app.core.generator import generator_service
from app.core.llm import llm_service
from app.database import create_db_and_tables, get_session
from app.models.article import Article


# Mock LLM
async def mock_generate_json(*args, **kwargs):
    return {
        "summary": "Test Summary",
        "outline": ["Intro"],
        "entities": [],
        "image_prompt": "Test Image",
        "image_caption": "Caption",
        "year": 2025,
        "timeline_event": "Event",
    }


# Side effect for generate_text to check if instructions were used
async def mock_generate_text(*args, **kwargs):
    prompt = args[0]
    # We can't easily check the prompt content here without parsing,
    # but we can return content that proves we were called.
    return "Generated Content"


llm_service.generate_json = MagicMock(side_effect=mock_generate_json)
llm_service.generate_text = MagicMock(side_effect=mock_generate_text)


def verify_custom_creation():
    print("Starting Custom Creation Verification...")

    world_name = "TestWorld_Custom"
    if os.path.exists(world_manager.get_world_path(world_name)):
        shutil.rmtree(world_manager.get_world_path(world_name))

    config = WorldConfig(name=world_name, generate_images=False)
    world_manager.create_world(config)
    create_db_and_tables(world_name)

    session_gen = get_session(world_name)
    session = next(session_gen)

    # Run Generation with Instructions
    print("Generating Article with Instructions...")
    instructions = "This article should be about a blue dragon."
    asyncio.run(
        generator_service.generate_article(
            world_name, "Blue Dragon", session, user_instructions=instructions
        )
    )

    # Verify that the instructions were passed to the LLM (via generate_json for planning)
    # generate_json is called for Planning AND Validation. We need to find the one with instructions.
    found = False
    for call in llm_service.generate_json.call_args_list:
        prompt_sent = call[0][0]
        if instructions in prompt_sent:
            found = True
            break

    if found:
        print("Instructions found in Plan Prompt: SUCCESS")
    else:
        print("Instructions NOT found in any Plan Prompt: FAILED")
        print("Calls made:", len(llm_service.generate_json.call_args_list))
        sys.exit(1)

    session.close()
    print("Custom Creation Verification Complete.")


if __name__ == "__main__":
    verify_custom_creation()
