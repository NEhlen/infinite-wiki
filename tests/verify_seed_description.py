import sys
import os
import shutil
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.getcwd())

from app.core.world import world_manager, WorldConfig
from app.core.generator import generator_service, ArticlePlan, DeduplicationResult
from app.core.llm import llm_service
from app.core.validator import ValidationOutput
from app.database import create_db_and_tables
from fastapi.testclient import TestClient
from app.main import app


# Mock LLM
async def mock_generate_json(*args, **kwargs):
    schema = kwargs.get("schema")
    if schema and schema.__name__ == "ValidationOutput":
        return ValidationOutput(is_valid=True, issues=[])
    if schema and schema.__name__ == "DeduplicationResult":
        return DeduplicationResult(is_duplicate=False, existing_title=None)

    # Default for Plan (ArticlePlan)
    return ArticlePlan(
        summary="Test Summary",
        outline=["Intro"],
        entities=[],
        image_prompt="Test Image",
        image_caption="Caption",
        year=2025,
        timeline_event="Event",
    )


async def mock_generate_text(*args, **kwargs):
    return "Generated Content"


llm_service.generate_json = MagicMock(side_effect=mock_generate_json)
llm_service.generate_text = MagicMock(side_effect=mock_generate_text)


def verify_seed_description():
    print("Starting Seed Description Verification...")

    world_name = "TestWorld_SeedDesc"
    if os.path.exists(world_manager.get_world_path(world_name)):
        shutil.rmtree(world_manager.get_world_path(world_name))

    client = TestClient(app)

    # Simulate Create World POST
    print("Simulating Create World POST...")
    response = client.post(
        "/create_world",
        data={
            "name": world_name,
            "description": "A test world",
            "system_prompt_planner": "You are a planner",
            "system_prompt_writer": "You are a writer",
            "system_prompt_image": "You are an artist",
            "seed_article_title": "The Seed",
            "seed_article_description": "This is the seed description.",
            "image_gen_model": "test-model",
            "generate_images": False,
        },
        follow_redirects=False,
    )

    if response.status_code == 303:
        print("World Creation Redirect: SUCCESS")
    else:
        print(f"World Creation Failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

    # Verify Instructions were passed to Planner
    found = False
    for call in llm_service.generate_json.call_args_list:
        prompt_sent = call[0][0]
        if "This is the seed description." in prompt_sent:
            found = True
            break

    if found:
        print("Seed Description passed to Planner: SUCCESS")
    else:
        print("Seed Description passed to Planner: FAILED")
        sys.exit(1)

    print("Seed Description Verification Complete.")


if __name__ == "__main__":
    verify_seed_description()
