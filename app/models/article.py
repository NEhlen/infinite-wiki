from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

class ArticleBase(SQLModel):
    title: str = Field(index=True)
    summary: str
    content: str
    image_url: Optional[str] = Field(default=None)
    image_caption: Optional[str] = Field(default=None)
    year: Optional[str] = Field(default=None)

class Article(ArticleBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # We might want to store relationships as a JSON string or separate table later
    # For now, let's keep it simple. The Graph will handle complex relations.
    related_entities_json: str = "[]" 

class ArticleCreate(ArticleBase):
    pass

class ArticleRead(ArticleBase):
    id: int
