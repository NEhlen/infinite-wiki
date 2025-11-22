from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Request,
    Form,
    Cookie,
    BackgroundTasks,
)
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Query
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

from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import status
import secrets

security = HTTPBasic(auto_error=False)


def get_current_username(
    credentials: Optional[HTTPBasicCredentials] = Depends(security),
):
    if not settings.AUTH_USERNAME or not settings.AUTH_PASSWORD:
        return "anonymous"

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = settings.AUTH_USERNAME.encode("utf8")
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )

    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = settings.AUTH_PASSWORD.encode("utf8")
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


from fastapi.staticfiles import StaticFiles

app = FastAPI(title=settings.APP_NAME, dependencies=[Depends(get_current_username)])
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# Inject base_url into all templates
@app.middleware("http")
async def add_base_url_context(request: Request, call_next):
    response = await call_next(request)
    return response


# We can't easily inject into TemplateResponse via middleware without monkeypatching or using a custom response class.
# Instead, let's just add it to the environment globals so it's available everywhere.
import os

base_url = os.getenv("BASE_URL", "")
templates.env.globals["base_url"] = base_url


@app.on_event("startup")
def on_startup():
    # Ensure default world exists if needed, or just ensure base dir
    pass


# --- World Management Routes ---


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    worlds = world_manager.list_worlds()
    return templates.TemplateResponse(
        "index.html", {"request": request, "worlds": worlds}
    )


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


@app.post("/create_world")
async def create_world(
    name: str = Form(...),
    description: str = Form(...),
    system_prompt_planner: str = Form(...),
    system_prompt_writer: str = Form(...),
    system_prompt_image: str = Form(...),
    seed_article_title: str = Form(...),
    seed_article_description: str = Form(None),
    image_gen_model: str = Form(...),
    generate_images: bool = Form(False),  # Default to False if unchecked
    background_tasks: BackgroundTasks = None,
):
    config = WorldConfig(
        name=name,
        description=description,
        system_prompt_planner=system_prompt_planner,
        system_prompt_writer=system_prompt_writer,
        system_prompt_image=system_prompt_image,
        image_gen_model=image_gen_model,
        generate_images=generate_images,
    )
    try:
        world_manager.create_world(config)
        create_db_and_tables(name)

        # Seed the first article
        session_gen = get_session(name)
        session = next(session_gen)
        try:
            await generator_service.generate_article(
                name,
                seed_article_title,
                session,
                background_tasks,
                skip_validation=True,
                user_instructions=seed_article_description,
            )
        finally:
            session.close()

        return RedirectResponse(
            url=f"/world/{name}/wiki/{seed_article_title}", status_code=303
        )
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

        return templates.TemplateResponse(
            "world_overview.html",
            {
                "request": request,
                "world_name": world_name,
                "world_config": world_config,
                "articles": articles,
            },
        )
    finally:
        session.close()


# --- Wiki Routes ---


@app.post("/world/{world_name}/create_custom")
async def create_custom_article(
    world_name: str,
    title: str = Form(...),
    description: str = Form(None),
    background_tasks: BackgroundTasks = None,
):
    session_gen = get_session(world_name)
    session = next(session_gen)
    try:
        # Check if exists
        statement = select(Article).where(Article.title == title)
        if session.exec(statement).first():
            return RedirectResponse(
                url=f"/world/{world_name}/wiki/{title}", status_code=303
            )

        article = await generator_service.generate_article(
            world_name, title, session, background_tasks, user_instructions=description
        )
        return RedirectResponse(
            url=f"/world/{world_name}/wiki/{article.title}", status_code=303
        )
    finally:
        session.close()


@app.get("/world/{world_name}/wiki/{title}", response_class=HTMLResponse)
async def get_wiki_page(
    request: Request,
    world_name: str,
    title: str,
    background_tasks: BackgroundTasks,
    skip_validation: Optional[bool] = Query(False, alias="skip-validation"),
):
    session_gen = get_session(world_name)
    session = next(session_gen)

    try:
        # Try to find existing
        statement = select(Article).where(Article.title == title)
        article = session.exec(statement).first()

        if not article:
            # Generate if not found
            article = await generator_service.generate_article(
                world_name,
                title,
                session,
                background_tasks,
                skip_validation=skip_validation,
            )

            # If deduplication returned a different article, redirect to it
            if article.title != title:
                return RedirectResponse(
                    url=f"/world/{world_name}/wiki/{article.title}", status_code=303
                )

        # Auto-link content
        from app.core.linker import linker_service

        linked_content = linker_service.autolink_content(world_name, article.content)

        # Convert Markdown to HTML
        html_content = markdown.markdown(linked_content)

        related = json.loads(article.related_entities_json)
        return templates.TemplateResponse(
            "article.html",
            {
                "request": request,
                "world_name": world_name,
                "article": article,
                "content_html": html_content,
                "related_entities": related,
                "generate_images": world_manager.get_config(world_name).generate_images,
            },
        )
    finally:
        session.close()


@app.get("/world/{world_name}/wiki/{title}/edit", response_class=HTMLResponse)
async def edit_wiki_page(request: Request, world_name: str, title: str):
    session_gen = get_session(world_name)
    session = next(session_gen)
    try:
        statement = select(Article).where(Article.title == title)
        article = session.exec(statement).first()

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        return templates.TemplateResponse(
            "article_edit.html",
            {
                "request": request,
                "world_name": world_name,
                "article": article,
                "content": article.content,
                "issues": [],
            },
        )
    finally:
        session.close()


@app.post("/world/{world_name}/wiki/{title}/edit", response_class=HTMLResponse)
async def save_wiki_edit(
    request: Request,
    world_name: str,
    title: str,
    content: str = Form(...),
    action: str = Form(...),
):
    session_gen = get_session(world_name)
    session = next(session_gen)
    try:
        statement = select(Article).where(Article.title == title)
        article = session.exec(statement).first()

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        if action == "force":
            # Skip validation, just save
            article.content = content
            session.add(article)
            session.commit()
            return RedirectResponse(
                url=f"/world/{world_name}/wiki/{title}", status_code=303
            )

        # Validate
        from app.core.validator import validator_service

        is_valid, issues = await validator_service.validate_article_update(
            world_name, article.content, content
        )

        if is_valid:
            article.content = content
            session.add(article)
            session.commit()
            return RedirectResponse(
                url=f"/world/{world_name}/wiki/{title}", status_code=303
            )
        else:
            return templates.TemplateResponse(
                "article_edit.html",
                {
                    "request": request,
                    "world_name": world_name,
                    "article": article,
                    "content": content,
                    "issues": issues,
                },
            )
    finally:
        session.close()


# --- Visualizer Routes ---


@app.get("/world/{world_name}/visualizers", response_class=HTMLResponse)
async def visualizers_page(request: Request, world_name: str):
    return templates.TemplateResponse(
        "visualizers.html", {"request": request, "world_name": world_name}
    )


@app.get("/api/world/{world_name}/graph_data")
async def get_graph_data(world_name: str):
    from app.core.graph import graph_service
    import networkx as nx

    graph = graph_service.get_graph(world_name)
    return nx.node_link_data(graph)


@app.get("/api/world/{world_name}/timeline_data")
async def get_timeline_data(world_name: str):
    from app.core.timeline import timeline_service

    events = timeline_service.get_context_events(world_name)
    return [
        {
            "id": e["name"],
            "name": e["name"],
            "content": e["name"],
            "year_numeric": e["year_numeric"],
            "display_date": e["display_date"],
            "description": e["description"],
            "type": e.get("type", "Unknown"),
        }
        for e in events
    ]


@app.get("/api/world/{world_name}/timeline/year/{year}")
async def get_timeline_year(world_name: str, year: str):
    from app.core.timeline import timeline_service

    return timeline_service.get_events_by_year(world_name, year)


@app.get("/api/world/{world_name}/timeline/nearby/{year}")
async def get_timeline_nearby(world_name: str, year: str, range: int = 10):
    from app.core.timeline import timeline_service

    return timeline_service.get_nearby_events(world_name, year, range)


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
