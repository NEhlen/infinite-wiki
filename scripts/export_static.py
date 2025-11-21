import os
import shutil
import json
from fastapi.testclient import TestClient
from app.main import app
from app.core.world import world_manager
from app.models.article import Article
from sqlmodel import select
from app.database import get_session

# Configuration
OUTPUT_DIR = "static_site"
# Use env var if set (e.g. from CI), otherwise default
BASE_URL = os.getenv("BASE_URL", "/infinite-wiki")


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def save_html(path, content):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def save_json(path, content):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2)


def export_static():
    print(f"Starting static export to {OUTPUT_DIR} with BASE_URL='{BASE_URL}'...")

    # Clean output dir
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    # Set BASE_URL in env for the app to pick up
    os.environ["BASE_URL"] = BASE_URL
    # We need to re-initialize templates or just rely on the fact that we set it in main.py
    # But main.py runs at import time.
    # Let's manually update the global in the imported app's templates
    from app.main import templates

    templates.env.globals["base_url"] = BASE_URL

    client = TestClient(app)

    # 1. Export Index
    print("Exporting Index...")
    resp = client.get("/")
    if resp.status_code == 200:
        save_html(os.path.join(OUTPUT_DIR, "index.html"), resp.text)
    else:
        print(f"Failed to fetch index: {resp.status_code}")

    # 2. Export Worlds
    worlds = world_manager.list_worlds()
    for world in worlds:
        print(f"Exporting World: {world}...")

        # World Home
        resp = client.get(f"/world/{world}")
        if resp.status_code == 200:
            save_html(os.path.join(OUTPUT_DIR, "world", world, "index.html"), resp.text)
        else:
            print(f"Failed to fetch world {world}: {resp.status_code}")

        # Visualizers
        resp = client.get(f"/world/{world}/visualizers")
        if resp.status_code == 200:
            save_html(
                os.path.join(OUTPUT_DIR, "world", world, "visualizers", "index.html"),
                resp.text,
            )

        # Graph Data
        resp = client.get(f"/api/world/{world}/graph_data")
        if resp.status_code == 200:
            save_json(
                os.path.join(OUTPUT_DIR, "api", "world", world, "graph_data"),
                resp.json(),
            )

        # Timeline Data
        resp = client.get(f"/api/world/{world}/timeline_data")
        if resp.status_code == 200:
            save_json(
                os.path.join(OUTPUT_DIR, "api", "world", world, "timeline_data"),
                resp.json(),
            )

        # Articles
        # We need to list all articles to export them
        # We can use the database directly since we have access
        session_gen = get_session(world)
        session = next(session_gen)
        try:
            statement = select(Article)
            articles = session.exec(statement).all()
            for article in articles:
                print(f"  Exporting Article: {article.title}")
                resp = client.get(f"/world/{world}/wiki/{article.title}")
                if resp.status_code == 200:
                    # Handle URL encoding in filename if needed, but usually browser handles it.
                    # However, for static files, we might want to be careful.
                    # Let's just save as is for now, assuming titles are file-system safe-ish or just simple text.
                    # If title has spaces, browser requests "Title%20Name".
                    # We should probably save as "Title Name/index.html" to match "/wiki/Title Name"

                    # Actually, if the link is /wiki/Foo%20Bar, the browser looks for folder Foo%20Bar or file Foo%20Bar.
                    # Let's try to match the URL structure exactly.

                    # If the title is "The Great Library", the URL is ".../wiki/The Great Library" (unencoded in href usually, but browser encodes it).
                    # If we save it as "The Great Library/index.html", then ".../wiki/The Great Library" works if server does directory index.
                    # GitHub Pages does directory index.

                    safe_title = (
                        article.title
                    )  # .replace(" ", "%20") ? No, FS usually handles spaces.

                    save_html(
                        os.path.join(
                            OUTPUT_DIR, "world", world, "wiki", safe_title, "index.html"
                        ),
                        resp.text,
                    )
                else:
                    print(
                        f"Failed to fetch article {article.title}: {resp.status_code}"
                    )
        finally:
            session.close()

        # Copy Images
        images_path = world_manager.get_images_path(world)
        if os.path.exists(images_path):
            dest_images_path = os.path.join(OUTPUT_DIR, "world", world, "images")
            if os.path.exists(dest_images_path):
                shutil.rmtree(dest_images_path)
            shutil.copytree(images_path, dest_images_path)
            print(f"  Copied images for {world}")

    # 3. Copy Static Assets (if any)
    # We don't have a static folder in app/ currently, but if we did:
    # if os.path.exists("app/static"):
    #     shutil.copytree("app/static", os.path.join(OUTPUT_DIR, "static"))

    print("Export complete.")


if __name__ == "__main__":
    export_static()
