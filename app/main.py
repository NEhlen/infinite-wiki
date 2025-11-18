from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from app.config import get_settings
from app.database import create_db_and_tables, get_session
from app.core.generator import generator_service
from app.models.article import Article, ArticleRead
import json

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("base.html", {"request": request, "content": "Welcome! Go to /wiki/Start to begin."})

@app.get("/wiki/{title}", response_class=HTMLResponse)
async def read_wiki(request: Request, title: str, session: Session = Depends(get_session)):
    # Try to find existing
    statement = select(Article).where(Article.title == title)
    article = session.exec(statement).first()
    
    if not article:
        # Generate if not found
        article = await generator_service.generate_article(title, session)
    
    # Convert Markdown to HTML
    import markdown
    html_content = markdown.markdown(article.content)
    
    # Create a copy or dict to avoid modifying the DB object if we were to save it back (though we aren't here)
    # But we need to pass it to the template. 
    # Let's just pass the html_content separately.
    
    related = json.loads(article.related_entities_json)
    return templates.TemplateResponse("article.html", {
        "request": request, 
        "article": article,
        "content_html": html_content,
        "related_entities": related
    })

# Keep API endpoints for debugging/programmatic access
@app.post("/api/generate/{title}", response_model=ArticleRead)
async def generate_article_api(title: str, session: Session = Depends(get_session)):
    article = await generator_service.generate_article(title, session)
    return article

@app.get("/api/article/{title}", response_model=ArticleRead)
async def get_article_api(title: str, session: Session = Depends(get_session)):
    statement = select(Article).where(Article.title == title)
    article = session.exec(statement).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
