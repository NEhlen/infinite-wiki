import os
import sys
import shutil
import asyncio
from sqlmodel import select

# Add project root to path
sys.path.append(os.getcwd())

from app.core.generator import generator_service
from app.core.world import world_manager, WorldConfig
from app.database import get_session, create_db_and_tables
from app.models.article import Article
from app.core.graph import graph_service


async def verify_deduplication():
    print("Verifying Deduplication Logic...")
    world_name = "dedup_test_world"

    # Setup world
    manager = world_manager
    if os.path.exists(manager.get_world_path(world_name)):
        shutil.rmtree(manager.get_world_path(world_name))
    manager.create_world(WorldConfig(name=world_name))
    create_db_and_tables(world_name)

    session_gen = get_session(world_name)
    session = next(session_gen)

    try:
        # 1. Create Base Article
        print("\n1. Creating Base Article: 'The Lost Commuters'")
        # Manually create to skip generation logic for the base
        article = Article(
            title="The Lost Commuters",
            summary="Test Summary",
            content="Test Content",
            year="2024",
        )
        session.add(article)
        session.commit()

        # 2. Test "The" Prefix Removal
        print("\n2. Testing 'Lost Commuters' (should match 'The Lost Commuters')...")
        result = await generator_service.generate_article(
            world_name, "Lost Commuters", session, skip_validation=True
        )
        if result.title == "The Lost Commuters":
            print("SUCCESS: Matched 'The Lost Commuters'")
        else:
            print(f"FAILED: Got '{result.title}'")
            sys.exit(1)

        # Verify Graph Alias
        graph = graph_service.get_graph(world_name)
        if (
            graph.has_node("Lost Commuters")
            and graph.nodes["Lost Commuters"].get("type") == "Alias"
        ):
            print("SUCCESS: Alias node created in graph.")
        else:
            print("FAILED: Alias node missing.")
            sys.exit(1)

        # 3. Test Case Insensitivity
        print("\n3. Testing 'the lost commuters' (case insensitive)...")
        result = await generator_service.generate_article(
            world_name, "the lost commuters", session, skip_validation=True
        )
        if result.title == "The Lost Commuters":
            print("SUCCESS: Matched 'The Lost Commuters'")
        else:
            print(f"FAILED: Got '{result.title}'")
            sys.exit(1)

        # 4. Test Markdown Stripping
        print("\n4. Testing '# The Lost Commuters' (markdown)...")
        result = await generator_service.generate_article(
            world_name, "# The Lost Commuters", session, skip_validation=True
        )
        if result.title == "The Lost Commuters":
            print("SUCCESS: Stripped markdown and matched.")
        else:
            print(f"FAILED: Got '{result.title}'")
            sys.exit(1)

    finally:
        session.close()
        # Cleanup
        if os.path.exists(manager.get_world_path(world_name)):
            shutil.rmtree(manager.get_world_path(world_name))


if __name__ == "__main__":
    asyncio.run(verify_deduplication())
