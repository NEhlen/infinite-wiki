import json
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.llm import llm_service
from app.core.rag import rag_service
from app.core.graph import graph_service
from app.core.image_gen import image_gen_service
from app.core.timeline import timeline_service
from app.models.article import Article
from app.config import get_settings

settings = get_settings()

class Entity(BaseModel):
    name: str
    type: str = Field(description="Person, Location, Organization, Event, Object, Concept, Technology")
    relation: str

class ArticlePlan(BaseModel):
    summary: str
    outline: List[str]
    entities: List[Entity]
    image_prompt: str = Field(description="Detailed visual description for sci-fi concept art based on the article topic.")
    year: Optional[str] = Field(description="Year or Era this article primarily relates to, if applicable.")
    timeline_event: Optional[str] = Field(description="Short description of the event for the timeline, if this article describes an event.")

class GeneratorService:
    async def generate_article(self, title: str, session: Session) -> Article:
        # 1. Check if article already exists
        statement = select(Article).where(Article.title == title)
        existing_article = session.exec(statement).first()
        if existing_article:
            return existing_article

        # 2. Gather Context
        rag_context = rag_service.query_context(title)
        graph_context = graph_service.get_context_subgraph([title])
        
        # 3. Stage 1: PLAN
        plan_prompt = f"""
        Plan a wiki article about "{title}".
        
        Context from similar articles:
        {rag_context}
        
        Context from Knowledge Graph:
        {graph_context}
        
        Goal: Create a consistent, interesting sci-fi world entry.
        """
        
        plan_response = await llm_service.generate_json(
            plan_prompt, 
            schema=ArticlePlan, 
            model=settings.LLM_MODEL,
            system_prompt=settings.SYSTEM_PROMPT_PLANNER
        )
        plan = ArticlePlan.model_validate(plan_response)
        
        # 4. Stage 2: WRITE
        write_prompt = f"""
        Write the full content for the wiki article "{title}" based on this plan:
        
        Summary: {plan.summary}
        Outline: {', '.join(plan.outline)}
        
        Context:
        {rag_context}
        
        Style: Encyclopedic, dry, descriptive, sci-fi. Use Markdown for formatting.
        """
        
        content = await llm_service.generate_text(
            write_prompt, 
            model=settings.LLM_MODEL,
            system_prompt=settings.SYSTEM_PROMPT_WRITER
        )
        
        # 5. Generate Image (using prompt from Plan)
        image_url = await image_gen_service.generate_image(plan.image_prompt, model=settings.IMAGE_GEN_MODEL)

        # 6. Save Article
        article = Article(
            title=title,
            summary=plan.summary,
            content=content,
            image_url=image_url,
            year=plan.year,
            related_entities_json=json.dumps([e.model_dump() for e in plan.entities])
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        
        # 7. Update Systems
        rag_service.add_article(article.title, article.content, article.id)
        
        # Update Graph
        graph_service.add_entity(title, "Article") 
        for entity in plan.entities:
            graph_service.add_entity(entity.name, entity.type)
            graph_service.add_relationship(title, entity.name, entity.relation)
            
        # Update Timeline
        if plan.year and plan.timeline_event:
            timeline_service.add_event(title, plan.year, plan.timeline_event)
            
        return article

generator_service = GeneratorService()
