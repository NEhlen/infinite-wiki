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
from fastapi.testclient import TestClient
from app.main import app


from app.core.generator import ArticlePlan, DeduplicationResult
from app.core.validator import ValidationOutput


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


def verify_selection_flow():
    print("Starting Selection Flow Verification...")

    world_name = "TestWorld_Selection"
    if os.path.exists(world_manager.get_world_path(world_name)):
        shutil.rmtree(world_manager.get_world_path(world_name))

    config = WorldConfig(name=world_name, generate_images=False)
    world_manager.create_world(config)
    create_db_and_tables(world_name)

    client = TestClient(app)

    # Simulate the POST request from the JS
    print("Simulating JS POST request...")
    response = client.post(
        f"/world/{world_name}/create_custom",
        data={
            "title": "Selected Text Title",
            "description": "User note from selection input",
        },
        follow_redirects=False,  # Don't follow redirects
    )

    # Check Redirect
    if response.status_code == 303:  # Redirect
        print("Redirect Status: SUCCESS")
        target_url = response.headers["location"]
        print(f"Redirect Target: {target_url}")
        assert (
            "Selected Text Title" in target_url
            or "Selected%20Text%20Title" in target_url
        )
    else:
        print(f"Redirect Status: FAILED (Got {response.status_code})")
        print(response.text)
        sys.exit(1)

    # Verify Instructions were passed (by checking mock calls)
    found = False
    for call in llm_service.generate_json.call_args_list:
        prompt_sent = call[0][0]
        if "User note from selection input" in prompt_sent:
            found = True
            break

    if found:
        print("Instructions passed to Planner: SUCCESS")
    else:
        print("Instructions passed to Planner: FAILED")
        sys.exit(1)

    print("Selection Flow Verification Complete.")


if __name__ == "__main__":
    verify_selection_flow()
