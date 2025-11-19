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

class RelatedEntity(BaseModel): # Renamed from Entity to RelatedEntity
    name: str
    type: str = Field(description="Person, Location, Organization, Event, Object, Concept, Technology")
    relation: str

class ArticlePlan(BaseModel):
    summary: str = Field(description="A concise summary of the article.")
    outline: List[str] = Field(description="A list of section headings for the article.")
    entities: List[RelatedEntity] = Field(description="List of related entities mentioned in the article.")
    image_prompt: str = Field(description="A detailed prompt for generating an image for this article.")
    image_caption: str = Field(description="A short caption for the generated image.")
    year: Optional[int] = Field(description="The year or era associated with this article, if applicable.")
    timeline_event: Optional[str] = Field(description="Short description of the event for the timeline, if this article describes an event.")

class GeneratorService:
    async def generate_article(self, world_name: str, title: str, session: Session) -> Article:
        # 1. Check if article already exists
        statement = select(Article).where(Article.title == title)
        existing_article = session.exec(statement).first()
        if existing_article:
            return existing_article

        # 2. Gather Context
        rag_context = rag_service.query_context(world_name, title)
        graph_context = graph_service.get_context_subgraph(world_name, [title])
        
        # Get World Config
        from app.core.world import world_manager
        world_config = world_manager.get_config(world_name)
        
        # 3. Stage 1: PLAN
        plan_prompt = f"""
        Plan a wiki article about "{title}".
        
        World Context:
        Name: {world_config.name}
        Description: {world_config.description}
        
        Context from similar articles:
        {rag_context}
        
        Context from Knowledge Graph:
        {graph_context}
        
        Goal: Create a consistent, interesting world entry that fits the world description. Stay within the world's canonical viewpoint, don't write from an external perspective.
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
        
        Style: Create an encyclopedic article that is both interesting and consistent with the world description. Use Markdown for formatting.
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
            image_caption=plan.image_caption,
            year=plan.year,
            related_entities_json=json.dumps([e.model_dump() for e in plan.entities])
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        
        # 7. Update Systems
        rag_service.add_article(world_name, article.title, article.content, article.id)
        
        # Update Graph
        graph_service.add_entity(world_name, title, "Article") 
        for entity in plan.entities:
            graph_service.add_entity(world_name, entity.name, entity.type)
            graph_service.add_relationship(world_name, title, entity.name, entity.relation)
            
        # Update Timeline
        if plan.year and plan.timeline_event:
            print("Adding timeline event:", plan.timeline_event, "for year:", plan.year)
            timeline_service.add_event(world_name, title, plan.year, plan.timeline_event)
            
        return article

generator_service = GeneratorService()
