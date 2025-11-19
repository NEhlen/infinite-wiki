import sys
import os
import asyncio
import shutil
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from app.main import app
from app.core.world import world_manager, WorldConfig
from app.database import create_db_and_tables, get_session
from app.models.article import Article
from app.core.llm import llm_service

client = TestClient(app)

# Mock LLM for validation
async def mock_validate_json(*args, **kwargs):
    prompt = args[0]
    if "INVALID_CONTENT" in prompt:
        return {"is_valid": False, "issues": ["Contradicts world lore."]}
    return {"is_valid": True, "issues": []}

llm_service.generate_json = MagicMock(side_effect=mock_validate_json)

def verify_edit_flow():
    print("Starting Edit Flow Verification...")
    
    world_name = "TestWorld_Edit"
    
    # 1. Clean up
    world_path = world_manager.get_world_path(world_name)
    if os.path.exists(world_path):
        shutil.rmtree(world_path)
        
    # 2. Create World & Article
    print(f"Creating world '{world_name}'...")
    config = WorldConfig(name=world_name)
    world_manager.create_world(config)
    create_db_and_tables(world_name)
    
    session_gen = get_session(world_name)
    session = next(session_gen)
    article = Article(title="Test Article", content="Original Content", summary="Summary", year="2025", related_entities_json="[]")
    session.add(article)
    session.commit()
    session.close()
    
    # 3. Test Valid Edit
    print("Testing Valid Edit...")
    response = client.post(
        f"/world/{world_name}/wiki/Test Article/edit",
        data={"content": "Valid New Content", "action": "validate"},
        follow_redirects=False
    )
    # Should redirect on success
    if response.status_code != 303:
        print(f"Failed Valid Edit. Status: {response.status_code}")
        print(f"Response: {response.text}")
    assert response.status_code == 303
    print("Valid Edit: SUCCESS")
    
    # 4. Test Invalid Edit (Triggering Mock)
    print("Testing Invalid Edit...")
    response = client.post(
        f"/world/{world_name}/wiki/Test Article/edit",
        data={"content": "INVALID_CONTENT", "action": "validate"}
    )
    # Should stay on page (200) and show issues
    assert response.status_code == 200
    assert "Contradicts world lore" in response.text
    print("Invalid Edit (Validation Caught): SUCCESS")
    
    # 5. Test Force Save
    print("Testing Force Save...")
    response = client.post(
        f"/world/{world_name}/wiki/Test Article/edit",
        data={"content": "INVALID_CONTENT_FORCED", "action": "force"},
        follow_redirects=False
    )
    # Should redirect
    assert response.status_code == 303
    
    # Verify content changed
    session = next(get_session(world_name))
    article = session.get(Article, 1)
    assert article.content == "INVALID_CONTENT_FORCED"
    session.close()
    print("Force Save: SUCCESS")
    
    print("Edit Flow Verification Complete.")

if __name__ == "__main__":
    verify_edit_flow()
