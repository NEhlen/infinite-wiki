import requests
import sys
import os
from sqlmodel import Session, select, create_engine

# Add app to path
sys.path.append(os.getcwd())

from app.core.graph import graph_service
from app.models.article import Article
from app.database import get_engine


def test_red_links():
    world_name = "modern-urban-horror"
    base_url = "http://127.0.0.1:8000"

    print(f"Testing Red Links for world: {world_name}")

    # 1. Create 'Red Link Test' via API to ensure it's in the running app's graph
    print("Creating 'Red Link Test' via API...")
    requests.post(
        f"{base_url}/world/{world_name}/create_custom",
        data={"title": "Red Link Test", "description": "Test"},
    )

    # 2. Create 'Missing Entity' via API
    print("Creating 'Missing Entity' via API...")
    requests.post(
        f"{base_url}/world/{world_name}/create_custom",
        data={"title": "Missing Entity", "description": "To be deleted"},
    )

    # 3. Delete 'Missing Entity' from DB but keep in Graph
    print("Deleting 'Missing Entity' from DB...")
    engine = get_engine(world_name)
    with Session(engine) as session:
        article = session.exec(
            select(Article).where(Article.title == "Missing Entity")
        ).first()
        if article:
            session.delete(article)
            session.commit()
            print("Deleted 'Missing Entity' from DB.")
        else:
            print("WARNING: 'Missing Entity' not found in DB!")

    # 4. Update 'Red Link Test' to mention 'Missing Entity'
    # We can do this by direct DB manipulation to avoid re-triggering generation
    print("Updating 'Red Link Test' content...")
    with Session(engine) as session:
        article = session.exec(
            select(Article).where(Article.title == "Red Link Test")
        ).first()
        if article:
            article.content = "This mentions Missing Entity in the text."
            session.add(article)
            session.commit()
            print("Updated 'Red Link Test'.")

    # 5. Fetch the page
    print("Fetching page...")
    try:
        response = requests.get(f"{base_url}/world/{world_name}/wiki/Red%20Link%20Test")
        response.raise_for_status()
        html = response.text

        # 6. Check HTML
        print("Checking HTML...")
        if 'class="new-article"' in html and 'data-title="Missing Entity"' in html:
            print("SUCCESS: Found 'new-article' class for Missing Entity.")
        else:
            print("FAILURE: Did NOT find 'new-article' class.")
            if "Missing Entity" in html:
                print("Found text but not class. Context:")
                start = html.find("Missing Entity") - 50
                end = start + 150
                print(html[start:end])
            else:
                print("Did not find 'Missing Entity' in HTML at all!")

    except Exception as e:
        print(f"Error fetching page: {e}")


if __name__ == "__main__":
    test_red_links()
