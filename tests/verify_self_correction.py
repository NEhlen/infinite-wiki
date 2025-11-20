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
from app.core.validator import validator_service
from app.database import create_db_and_tables, get_session
from app.models.article import Article
from sqlmodel import select


# Mock Validator
async def mock_validate(*args, **kwargs):
    content = args[2]  # new_content
    if "Bad Content" in content:
        return False, ["Content is bad."]
    return True, []


validator_service.validate_article_update = MagicMock(side_effect=mock_validate)


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


# Side effect for generate_text to simulate rewrite
text_gen_call_count = 0


async def mock_generate_text(*args, **kwargs):
    global text_gen_call_count
    text_gen_call_count += 1
    prompt = args[0]

    if "Rewrite the article" in prompt:
        return "Good Content (Rewritten)"

    return "Bad Content"


llm_service.generate_json = MagicMock(side_effect=mock_generate_json)
llm_service.generate_text = MagicMock(side_effect=mock_generate_text)


def verify_self_correction():
    print("Starting Self-Correction Verification...")

    world_name = "TestWorld_Correction"
    if os.path.exists(world_manager.get_world_path(world_name)):
        shutil.rmtree(world_manager.get_world_path(world_name))

    config = WorldConfig(name=world_name, generate_images=False)
    world_manager.create_world(config)
    create_db_and_tables(world_name)

    session_gen = get_session(world_name)
    session = next(session_gen)

    # Run Generation
    print("Generating Article...")
    asyncio.run(generator_service.generate_article(world_name, "Test Article", session))

    # Verify
    article = session.get(Article, 1)
    print(f"Final Content: {article.content}")

    assert article.content == "Good Content (Rewritten)"
    assert (
        validator_service.validate_article_update.call_count == 2
    )  # Once for Bad, Once for Good

    print("Self-Correction Verification: SUCCESS")

    # Test Skip Validation
    print("Testing Skip Validation...")
    validator_service.validate_article_update.reset_mock()
    llm_service.generate_text.reset_mock()

    # Force "Bad Content" but skip validation
    # We need a new article title
    asyncio.run(
        generator_service.generate_article(
            world_name, "Skipped Article", session, skip_validation=True
        )
    )

    skipped_article = session.exec(
        select(Article).where(Article.title == "Skipped Article")
    ).first()
    assert skipped_article.content == "Bad Content"  # Should not be rewritten
    assert validator_service.validate_article_update.call_count == 0

    print("Skip Validation Verification: SUCCESS")

    session.close()


if __name__ == "__main__":
    verify_self_correction()
