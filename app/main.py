from fastapi import FastAPI, Depends, HTTPException, Request, Form, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from typing import Optional
import json
import markdown

from app.config import get_settings
from app.database import create_db_and_tables, get_session
from app.core.generator import generator_service
from app.models.article import Article, ArticleRead
from app.core.world import world_manager, WorldConfig

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def on_startup():
    # Ensure default world exists if needed, or just ensure base dir
    pass

# --- World Management Routes ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    worlds = world_manager.list_worlds()
    return templates.TemplateResponse("index.html", {"request": request, "worlds": worlds})

@app.get("/world/create", response_class=HTMLResponse)
async def create_world_page(request: Request):
    return templates.TemplateResponse("world_create.html", {"request": request})

from app.core.magic import magic_service
from pydantic import BaseModel

class MagicRequest(BaseModel):
    prompt: str

@app.post("/api/magic/config")
async def magic_config(req: MagicRequest):
    config = await magic_service.generate_config(req.prompt)
    return config

@app.post("/world/create")
async def create_world(
    name: str = Form(...),
    description: str = Form(""),
    system_prompt_planner: str = Form("You are a creative world-building assistant."),
    system_prompt_writer: str = Form("You are an encyclopedic writer."),
    system_prompt_image: str = Form("You are an expert art director."),
    seed_article_title: str = Form("The Beginning"),
    llm_model: str = Form("grok-4-fast-reasoning-latest"),
    image_gen_model: str = Form("grok-2-image-latest")
):
    config = WorldConfig(
        name=name,
        description=description,
        system_prompt_planner=system_prompt_planner,
        system_prompt_writer=system_prompt_writer,
        system_prompt_image=system_prompt_image,
        llm_model=llm_model,
        image_gen_model=image_gen_model
    )
    try:
        world_manager.create_world(config)
        create_db_and_tables(name) # Initialize DB for new world
        # Redirect to the seed article to trigger generation
        return RedirectResponse(url=f"/world/{name}/wiki/{seed_article_title}", status_code=303)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/world/{world_name}", response_class=HTMLResponse)
async def world_home(request: Request, world_name: str):
    session_gen = get_session(world_name)
    session = next(session_gen)
    try:
        statement = select(Article).order_by(Article.title)
        articles = session.exec(statement).all()
        
        world_config = world_manager.get_config(world_name)
        
        return templates.TemplateResponse("world_overview.html", {
            "request": request, 
            "world_name": world_name,
            "world_config": world_config,
            "articles": articles
        })
    finally:
        session.close()

# --- Wiki Routes ---

@app.get("/world/{world_name}/wiki/{title}", response_class=HTMLResponse)
async def read_wiki(request: Request, world_name: str, title: str):
    session_gen = get_session(world_name)
    session = next(session_gen)
    
    try:
        # Try to find existing
        statement = select(Article).where(Article.title == title)
        article = session.exec(statement).first()
        
        if not article:
            # Generate if not found
            article = await generator_service.generate_article(world_name, title, session)
        
        # Auto-link content
        from app.core.linker import linker_service
        linked_content = linker_service.autolink_content(world_name, article.content)
        
        # Convert Markdown to HTML
        html_content = markdown.markdown(linked_content)
        
        related = json.loads(article.related_entities_json)
        return templates.TemplateResponse("article.html", {
            "request": request, 
            "world_name": world_name,
            "article": article,
            "content_html": html_content,
            "related_entities": related
        })
    finally:
        session.close()

# --- Visualizer Routes ---

@app.get("/world/{world_name}/visualizers", response_class=HTMLResponse)
async def visualizers_page(request: Request, world_name: str):
    return templates.TemplateResponse("visualizers.html", {"request": request, "world_name": world_name})

@app.get("/api/world/{world_name}/graph_data")
async def get_graph_data(world_name: str):
    from app.core.graph import graph_service
    import networkx as nx
    graph = graph_service.get_graph(world_name)
    print("Graph data:", nx.node_link_data(graph))
    return nx.node_link_data(graph)

@app.get("/api/world/{world_name}/timeline_data")
async def get_timeline_data(world_name: str):
    from app.core.timeline import timeline_service
    # Get all events. For now, we can just get a large window or implement a "get all" method.
    # Let's use the existing get_context_events but with a hack or update it.
    # Actually, let's just iterate the graph here for simplicity as we did in timeline service.
    from app.core.graph import graph_service
    
    events = []
    graph = graph_service.get_graph(world_name)
    for node, data in graph.nodes(data=True):
        if data.get("type") == "Event" and "year" in data:
            print(data)
            # Vis.js Timeline expects {id, content, start}
            # Try to parse year
            start_date = data["year"]
            try:
                # If it's just a year number, convert to YYYY-01-01
                year_int = int(str(start_date).strip())
                start_date = f"{year_int:04d}-01-01"
            except ValueError:
                # If not a number, we might need a fallback or just let Vis.js try (it will likely fail/show current date)
                # For now, let's skip non-numeric years or put them at a default far future?
                # Or better: don't add them to the timeline if we can't parse the year.
                continue
                
            events.append({
                "id": node, 
                "content": node, 
                "start": start_date, 
                "title": data.get("description", "")
            })
    print("Timeline data:", events)
    return events

@app.get("/world/{world_name}/images/{filename}")
async def get_world_image(world_name: str, filename: str):
    import os
    from fastapi.responses import FileResponse
    
    image_path = os.path.join(world_manager.get_images_path(world_name), filename)
    if os.path.exists(image_path):
        return FileResponse(image_path)
    else:
        raise HTTPException(status_code=404, detail="Image not found")

# --- API Routes ---

@app.post("/api/world/{world_name}/generate/{title}", response_model=ArticleRead)
async def generate_article_api(world_name: str, title: str):
    session_gen = get_session(world_name)
    session = next(session_gen)
    try:
        article = await generator_service.generate_article(world_name, title, session)
        return article
    finally:
        session.close()

@app.get("/api/world/{world_name}/article/{title}", response_model=ArticleRead)
async def get_article_api(world_name: str, title: str):
    session_gen = get_session(world_name)
    session = next(session_gen)
    try:
        statement = select(Article).where(Article.title == title)
        article = session.exec(statement).first()
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        return article
    finally:
        session.close()
