import json
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import BackgroundTasks

from app.core.llm import llm_service
from app.core.rag import rag_service
from app.core.graph import graph_service
from app.core.image_gen import image_gen_service
from app.core.timeline import timeline_service
from app.core.validator import validator_service
from app.models.article import Article
from app.config import get_settings

settings = get_settings()


class RelatedEntity(BaseModel):  # Renamed from Entity to RelatedEntity
    name: str
    type: str = Field(
        description="Person, Location, Organization, Event, Object, Concept, Technology"
    )
    relation: str


class ArticlePlan(BaseModel):
    summary: str = Field(description="A concise summary of the article.")
    outline: List[str] = Field(
        description="A list of section headings for the article."
    )
    entities: List[RelatedEntity] = Field(
        description="List of related entities mentioned in the article."
    )
    image_prompt: str = Field(
        description="A detailed prompt for generating an image for this article."
    )
    image_caption: str = Field(description="A short caption for the generated image.")
    year: Optional[int] = Field(
        description="The year or era associated with this article, if applicable."
    )
    timeline_event: Optional[str] = Field(
        description="Short description of the event for the timeline, if this article describes an event or there is a clear 'major event' in the article."
    )


class DeduplicationResult(BaseModel):
    is_duplicate: bool = Field(
        description="True if the requested title refers to an existing entity."
    )
    existing_title: Optional[str] = Field(
        description="The title of the existing entity if is_duplicate is True."
    )


class GeneratorService:
    async def generate_article(
        self,
        world_name: str,
        title: str,
        session: Session,
        background_tasks: BackgroundTasks = None,
        skip_validation: bool = False,
        user_instructions: Optional[str] = None,
    ) -> Article:
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

        # 2.5 Deduplication Check
        if rag_context:
            dedup_prompt = f"""
            Check if the requested article title "{title}" refers to the same entity as any of the existing articles below.
            
            Existing Articles (Context):
            {rag_context}
            
            If "{title}" is clearly an alias, variation, or the same entity as one of the existing articles, return true and the existing title.
            If it is a new, distinct entity, return false.
            """

            dedup_response = await llm_service.generate_json(
                dedup_prompt,
                schema=DeduplicationResult,
                model=world_config.llm_model,
                system_prompt="You are a helpful assistant that prevents duplicate wiki entries.",
            )

            if dedup_response.is_duplicate and dedup_response.existing_title:
                print(
                    f"Deduplication: '{title}' identified as duplicate of '{dedup_response.existing_title}'"
                )

                # Add Alias to Graph
                graph_service.add_entity(world_name, title, "Alias")
                graph_service.add_relationship(
                    world_name, title, dedup_response.existing_title, "is_alias_of"
                )

                # Fetch existing
                statement = select(Article).where(
                    Article.title == dedup_response.existing_title
                )
                existing_article = session.exec(statement).first()
                if existing_article:
                    return existing_article

        # 3. Stage 1: PLAN
        instructions_text = ""
        if user_instructions:
            instructions_text = (
                f"\nUser Instructions/Description:\n{user_instructions}\n"
            )

        plan_prompt = f"""
        Plan a wiki article about "{title}".
        
        World Context:
        Name: {world_config.name}
        Description: {world_config.description}
        {instructions_text}
        Context from similar articles:
        {rag_context}
        
        Context from Knowledge Graph:
        {graph_context}
        
        Goal: Create a consistent, interesting world entry that fits the world description. Stay within the world's canonical viewpoint, don't write from an external perspective.
        """
        print(
            f"Using Config: Planner='{world_config.system_prompt_planner[:20]}...', Writer='{world_config.system_prompt_writer[:20]}...', Model='{world_config.llm_model}'"
        )

        plan_response = await llm_service.generate_json(
            plan_prompt,
            schema=ArticlePlan,
            model=world_config.llm_model,
            system_prompt=world_config.system_prompt_planner,
        )
        plan = ArticlePlan.model_validate(plan_response)

        # 4. Stage 2: WRITE
        write_prompt = f"""
        Write the full content for the wiki article "{title}" based on this plan:

        World Context:
        Name: {world_config.name}
        Description: {world_config.description}
        
        Summary: {plan.summary}
        Outline: {', '.join(plan.outline)}
        
        Context:
        {rag_context}
        
        Style: Create an article that is both interesting and consistent with the world description and your system prompt. Write from an in-universe perspective. Use Markdown for formatting.
        """

        content = await llm_service.generate_text(
            write_prompt,
            model=world_config.llm_model,
            system_prompt=world_config.system_prompt_writer,
        )

        # 4.5. Validation & Rewrite Loop
        if not skip_validation:
            max_retries = 2
            for attempt in range(max_retries):
                print(
                    f"Validating generated content (Attempt {attempt + 1}/{max_retries})..."
                )
                is_valid, issues = await validator_service.validate_article_update(
                    world_name, "", content
                )

                if is_valid:
                    print("Content validation passed.")
                    break

                print(f"Validation failed with issues: {issues}. Rewriting...")

                rewrite_prompt = f"""
                The following article content was generated but failed consistency validation.
                
                Original Plan Summary: {plan.summary}
                
                Current Content:
                {content}
                
                Validation Issues:
                {json.dumps(issues, indent=2)}
                
                Task: Rewrite the article to address the validation issues while maintaining the original plan and style.
                Ensure the new content is consistent with the world context.
                """

                content = await llm_service.generate_text(
                    rewrite_prompt,
                    model=world_config.llm_model,
                    system_prompt=world_config.system_prompt_writer,
                )
            else:
                print("Max validation retries reached. Saving best effort.")

        # 5. Save Article (Initially without image)
        article = Article(
            title=title,
            summary=plan.summary,
            content=content,
            image_url=None,  # Will be updated in background if enabled
            image_caption=plan.image_caption,
            year=plan.year,
            related_entities_json=json.dumps([e.model_dump() for e in plan.entities]),
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        # 6. Handle Image Generation
        if world_config.generate_images:
            if background_tasks:
                background_tasks.add_task(
                    self.generate_and_save_image,
                    world_name,
                    article.id,
                    plan.image_prompt,
                    world_config,
                )
            else:
                # Fallback to sync if no background tasks provided (e.g. in tests or scripts)
                await self.generate_and_save_image(
                    world_name, article.id, plan.image_prompt, world_config
                )

        # 7. Update Systems
        rag_service.add_article(world_name, article.title, article.content, article.id)

        # Update Graph
        graph_service.add_entity(world_name, title, "Article")
        for entity in plan.entities:
            graph_service.add_entity(world_name, entity.name, entity.type)
            graph_service.add_relationship(
                world_name, title, entity.name, entity.relation
            )

        # Update Timeline
        if plan.year and plan.timeline_event:
            print("Adding timeline event:", plan.timeline_event, "for year:", plan.year)
            timeline_service.add_event(
                world_name, title, plan.year, plan.timeline_event
            )

        return article

    async def generate_and_save_image(
        self, world_name: str, article_id: int, image_prompt: str, world_config
    ):
        print(f"Starting background image generation for article {article_id}...")
        from app.database import get_session

        # Optimize prompt
        optimized_prompt = await image_gen_service.optimize_image_prompt(
            image_prompt, world_config.system_prompt_image, model=world_config.llm_model
        )

        # Generate
        print("optimized_image_prompt: ", optimized_prompt)
        image_b64 = await image_gen_service.generate_image(
            optimized_prompt,
            model=world_config.image_gen_model,
            response_format="b64_json",
        )

        image_url = None
        if image_b64 and not image_b64.startswith("http"):
            # Decode and save locally
            import base64
            import os
            from app.core.world import world_manager

            # We need to get the title again to make the filename, or just use ID?
            # Let's fetch the article to be safe and get the title
            session_gen = get_session(world_name)
            session = next(session_gen)
            try:
                article = session.get(Article, article_id)
                if not article:
                    print(f"Article {article_id} not found for image update.")
                    return

                # Create safe filename
                safe_title = (
                    "".join(
                        [
                            c
                            for c in article.title
                            if c.isalnum() or c in (" ", "-", "_")
                        ]
                    )
                    .strip()
                    .replace(" ", "_")
                )
                filename = f"{safe_title}.png"

                images_dir = world_manager.get_images_path(world_name)
                filepath = os.path.join(images_dir, filename)

                try:
                    with open(filepath, "wb") as f:
                        f.write(base64.b64decode(image_b64))

                    # Store relative path
                    image_url = f"/world/{world_name}/images/{filename}"

                    # Update Article
                    article.image_url = image_url
                    session.add(article)
                    session.commit()
                    print(f"Image saved and article updated for {article.title}")

                except Exception as e:
                    print(f"Failed to save image: {e}")
            finally:
                session.close()
        else:
            print(
                "Image generation failed or returned URL (not supported for local save yet)."
            )


generator_service = GeneratorService()
