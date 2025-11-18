import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from app.core.generator import generator_service, ArticlePlan, Entity
from app.database import create_db_and_tables, get_session
from app.models.article import Article

async def verify_flow():
    print("Starting verification (Round 2)...")
    
    # Mock LLM Plan Response
    mock_plan = ArticlePlan(
        summary="A test summary for v2",
        outline=["Introduction", "History", "Conclusion"],
        entities=[Entity(name="Test Entity V2", type="Location", relation="Located in")],
        image_prompt="A futuristic city skyline",
        year="2150",
        timeline_event="Foundation of the city"
    )
    
    # Mock LLM Write Response
    mock_content = "# Test Article V2\n\nThis is the content generated based on the plan."
    
    with patch("app.core.llm.llm_service.generate_json", new_callable=AsyncMock) as mock_generate_json, \
         patch("app.core.llm.llm_service.generate_text", new_callable=AsyncMock) as mock_generate_text, \
         patch("app.core.image_gen.image_gen_service.generate_image", new_callable=AsyncMock) as mock_generate_image:
        
        # Setup mocks
        mock_generate_json.return_value = mock_plan.model_dump()
        mock_generate_text.return_value = mock_content
        mock_generate_image.return_value = "http://example.com/image_v2.png"
        
        # Setup DB
        create_db_and_tables()
        session_gen = get_session()
        session = next(session_gen)
        
        print("Generating article 'Test Article V2'...")
        article = await generator_service.generate_article("Test Article V2", session)
        
        print(f"Article Generated: {article.title}")
        print(f"Summary: {article.summary}")
        print(f"Image URL: {article.image_url}")
        print(f"Year: {article.year}")
        
        assert article.title == "Test Article V2"
        assert article.summary == "A test summary for v2"
        assert article.image_url == "http://example.com/image_v2.png"
        assert article.year == "2150"
        
        print("Verification Successful!")

if __name__ == "__main__":
    asyncio.run(verify_flow())
