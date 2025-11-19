import sys
import os
import asyncio
import shutil

# Add project root to path
sys.path.append(os.getcwd())

from app.core.world import world_manager, WorldConfig
from app.database import create_db_and_tables, get_session
from app.core.generator import generator_service
from app.models.article import Article
from sqlmodel import select

# Mock LLM and Image Gen to avoid API costs/keys during test
from unittest.mock import MagicMock
from app.core.llm import llm_service
from app.core.image_gen import image_gen_service

async def mock_generate_json(*args, **kwargs):
    # Return a mock ArticlePlan
    return {
        "summary": "A test summary for V2.",
        "outline": ["Introduction", "History", "Conclusion"],
        "entities": [
            {"name": "Related Entity A", "type": "Person", "relation": "founder"},
            {"name": "Related Entity B", "type": "Location", "relation": "capital"}
        ],
        "image_prompt": "A test image prompt",
        "year": "2200",
        "timeline_event": "The founding of the test entity."
    }

async def mock_generate_text(*args, **kwargs):
    return "This is the content of the test article. It mentions Related Entity A and Related Entity B."

async def mock_generate_image(*args, **kwargs):
    return "http://example.com/image_v2.png"

llm_service.generate_json = MagicMock(side_effect=mock_generate_json)
llm_service.generate_text = MagicMock(side_effect=mock_generate_text)
image_gen_service.generate_image = MagicMock(side_effect=mock_generate_image)

async def verify_v2():
    print("Starting V2 Verification...")
    
    world_name = "TestWorld_V2"
    
    # 1. Clean up previous test run
    world_path = world_manager.get_world_path(world_name)
    if os.path.exists(world_path):
        shutil.rmtree(world_path)
    
    # 2. Create World
    print(f"Creating world '{world_name}'...")
    config = WorldConfig(
        name=world_name,
        description="A test world for V2 verification.",
        system_prompt_planner="Planner Prompt",
        system_prompt_writer="Writer Prompt",
        system_prompt_image="Image Prompt"
    )
    world_manager.create_world(config)
    create_db_and_tables(world_name)
    
    # 3. Generate Article
    print("Generating article 'Test Article'...")
    session_gen = get_session(world_name)
    session = next(session_gen)
    
    try:
        article = await generator_service.generate_article(world_name, "Test Article", session)
        print(f"Article Generated: {article.title}")
        print(f"Summary: {article.summary}")
        print(f"Year: {article.year}")
        
        # 4. Verify Auto-linking
        # The content returned by generator is raw markdown. 
        # Auto-linking happens in the view (main.py), but we can test the linker service directly.
        from app.core.linker import linker_service
        linked_content = linker_service.autolink_content(world_name, article.content)
        print(f"Linked Content: {linked_content}")
        
        if "[Related Entity A](/world/TestWorld_V2/wiki/Related%20Entity%20A)" in linked_content:
            print("Auto-linking: SUCCESS")
        else:
            print("Auto-linking: FAILED")
            
        # 5. Verify Graph Data
        from app.core.graph import graph_service
        graph = graph_service.get_graph(world_name)
        if graph.has_node("Test Article") and graph.has_node("Related Entity A"):
            print("Graph Verification: SUCCESS")
        else:
            print("Graph Verification: FAILED")
            
        # 6. Verify Timeline Data
        # We can check if the event was added to the graph with year
        if graph.nodes["Test Article"].get("year") == "2200":
             print("Timeline Verification: SUCCESS")
        else:
             print("Timeline Verification: FAILED (Year missing or incorrect)")

    finally:
        session.close()
        
    print("V2 Verification Complete.")

if __name__ == "__main__":
    asyncio.run(verify_v2())
