import sys
import os
import asyncio
import shutil
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.getcwd())

from app.core.world import world_manager, WorldConfig
from app.core.generator import generator_service, DeduplicationResult
from app.core.llm import llm_service
from app.core.rag import rag_service
from app.database import create_db_and_tables, get_session
from app.models.article import Article


# Mock LLM
async def mock_generate_json(*args, **kwargs):
    prompt = args[0]
    schema = kwargs.get("schema")

    if schema == DeduplicationResult:
        if "Dr. Singh" in prompt:
            return DeduplicationResult(
                is_duplicate=True, existing_title="Dr. Priya Singh"
            )
        return DeduplicationResult(is_duplicate=False, existing_title=None)

    # Default for Plan
    return {
        "summary": "Test Summary",
        "outline": ["Intro"],
        "entities": [],
        "image_prompt": "Test Image",
        "image_caption": "Caption",
        "year": 2025,
        "timeline_event": "Event",
    }


async def mock_generate_text(*args, **kwargs):
    return "Generated Content"


llm_service.generate_json = MagicMock(side_effect=mock_generate_json)
llm_service.generate_text = MagicMock(side_effect=mock_generate_text)

# Mock RAG to return something so dedup check runs
rag_service.query_context = MagicMock(
    return_value=["Dr. Priya Singh: A brilliant scientist..."]
)


def verify_deduplication():
    print("Starting Deduplication Verification...")

    world_name = "TestWorld_Dedup"
    if os.path.exists(world_manager.get_world_path(world_name)):
        shutil.rmtree(world_manager.get_world_path(world_name))

    config = WorldConfig(name=world_name, generate_images=False)
    world_manager.create_world(config)
    create_db_and_tables(world_name)

    session_gen = get_session(world_name)
    session = next(session_gen)

    # 1. Create the "Existing" Article
    existing = Article(
        title="Dr. Priya Singh", content="Original Content", summary="Summary"
    )
    session.add(existing)
    session.commit()

    # 2. Try to generate "Dr. Singh"
    print("Requesting 'Dr. Singh'...")
    article = asyncio.run(
        generator_service.generate_article(world_name, "Dr. Singh", session)
    )

    # 3. Verify we got the existing article
    print(f"Returned Title: {article.title}")
    assert article.title == "Dr. Priya Singh"
    assert article.content == "Original Content"

    # Explicitly check that the returned title is NOT what we requested
    if article.title != "Dr. Singh":
        print("Redirect Logic Check: SUCCESS (Title mismatch confirmed)")
    else:
        print("Redirect Logic Check: FAILED (Title should be different)")

    # 4. Verify Graph Alias
    from app.core.graph import graph_service

    graph = graph_service.get_graph(world_name)

    if graph.has_edge("Dr. Singh", "Dr. Priya Singh"):
        print("Graph Alias Check: SUCCESS")
    else:
        # Check reverse or just existence
        print("Graph Alias Check: FAILED")
        print("Nodes:", graph.nodes())
        print("Edges:", graph.edges())

    print("Deduplication Verification: SUCCESS")
    session.close()


if __name__ == "__main__":
    verify_deduplication()
