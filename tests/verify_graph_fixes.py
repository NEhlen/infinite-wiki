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
from app.core.timeline import timeline_service


async def verify_graph_fixes():
    print("Verifying Graph Fixes...")
    world_name = "graph_fix_test_world"

    # Setup world
    manager = world_manager
    if os.path.exists(manager.get_world_path(world_name)):
        shutil.rmtree(manager.get_world_path(world_name))
    manager.create_world(WorldConfig(name=world_name))
    create_db_and_tables(world_name)

    session_gen = get_session(world_name)
    session = next(session_gen)

    try:
        # 1. Test Unified Timeline Node
        print("\n1. Testing Unified Timeline Node...")
        # Create an article with timeline data manually (simulating generation)
        article_title = "The Big Event"
        article = Article(
            title=article_title, summary="Summary", content="Content", year="2025"
        )
        session.add(article)
        session.commit()

        # Add to graph as Article with timeline attributes
        graph_service.add_entity(
            world_name,
            article_title,
            "Article",
            attributes={
                "year_numeric": 2025.0,
                "display_date": "2025",
                "description": "Something big happened.",
            },
        )

        # Verify Timeline Service picks it up
        events = timeline_service.get_context_events(world_name)
        found = False
        for event in events:
            if event["name"] == article_title and event["year_numeric"] == 2025.0:
                found = True
                print("SUCCESS: Article node found in timeline events.")
                break

        if not found:
            print("FAILED: Article node NOT found in timeline events.")
            print("Events found:", events)
            sys.exit(1)

        # 2. Test Alias Type Update
        print("\n2. Testing Alias Type Update...")
        # Create a placeholder node (simulating a mention)
        placeholder_name = "Flicker"
        graph_service.add_entity(world_name, placeholder_name, "Placeholder")

        # Create the target article
        target_title = "Flicker Phenomena"
        target_article = Article(
            title=target_title, summary="Summary", content="Content"
        )
        session.add(target_article)
        session.commit()

        # Trigger deduplication (heuristic)
        # We expect "Flicker" to match "Flicker Phenomena" via "The" check or just partial match?
        # Wait, "Flicker" -> "Flicker Phenomena" is not a "The" match.
        # But "The Flicker" -> "Flicker" is.
        # Let's test the "The" match specifically as that triggers the alias update logic we changed.

        # Create "The Flicker" article which should alias to "Flicker" (if Flicker existed)
        # Actually, let's test the exact scenario: "Flicker" (alias) -> "Flicker Phenomena" (target)
        # This requires the LLM or a manual alias setup.
        # Let's test the code path we changed: Heuristic "The" check.

        # Create "The Real Thing" article
        real_title = "The Real Thing"
        real_article = Article(title=real_title, summary="S", content="C")
        session.add(real_article)
        session.commit()

        # Create placeholder for "Real Thing" (simulating it existing as a generic node)
        alias_title = "Real Thing"
        graph_service.add_entity(world_name, alias_title, "GenericNode")

        # Generate "Real Thing" -> Should match "The Real Thing" and update node type
        print(f"Generating '{alias_title}' (should alias to '{real_title}')...")
        result = await generator_service.generate_article(
            world_name, alias_title, session, skip_validation=True
        )

        if result.title == real_title:
            print(f"SUCCESS: Redirected to '{real_title}'")

            # Verify Graph Node Type
            graph = graph_service.get_graph(world_name)
            node = graph.nodes[alias_title]
            if node.get("type") == "Alias":
                print("SUCCESS: Node type updated to 'Alias'")
            else:
                print(f"FAILED: Node type is '{node.get('type')}'")
                sys.exit(1)
        else:
            print(f"FAILED: Did not redirect. Got '{result.title}'")
            sys.exit(1)

    finally:
        session.close()
        # Cleanup
        if os.path.exists(manager.get_world_path(world_name)):
            shutil.rmtree(manager.get_world_path(world_name))


if __name__ == "__main__":
    asyncio.run(verify_graph_fixes())
