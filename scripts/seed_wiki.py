import asyncio
import sys
import os
import argparse

# Add project root to path
sys.path.append(os.getcwd())

from app.core.generator import generator_service
from app.database import create_db_and_tables, get_session

async def seed_wiki(topic: str):
    print(f"Seeding wiki with topic: {topic}")
    create_db_and_tables()
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        article = await generator_service.generate_article(topic, session)
        print(f"Successfully generated article: {article.title}")
        print(f"Summary: {article.summary}")
        print(f"Image URL: {article.image_url}")
    except Exception as e:
        print(f"Error seeding wiki: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the Infinite Wiki with a starting topic.")
    parser.add_argument("topic", type=str, help="The topic of the first article.")
    args = parser.parse_args()
    
    asyncio.run(seed_wiki(args.topic))
