from typing import List, Tuple
from app.core.llm import llm_service
from app.core.rag import rag_service
from app.core.world import world_manager
from pydantic import BaseModel


class ValidationOutput(BaseModel):
    is_valid: bool
    issues: List[str]


class ValidatorService:
    async def validate_article_update(
        self, world_name: str, old_content: str, new_content: str
    ) -> Tuple[bool, List[str]]:
        """
        Validates changes to an article against the world context.
        Returns (is_valid, list_of_issues).
        """
        # 1. Get World Config
        config = world_manager.get_config(world_name)

        # 2. Get RAG Context (checking against other articles)
        # We query using the new content to see if it contradicts existing knowledge
        context_docs = rag_service.query_context(world_name, new_content, n_results=3)
        context_text = "\n\n".join(context_docs)

        # 3. Construct Prompt
        prompt = f"""
        You are a consistency checker for a fictional world wiki.
        
        World Description: {config.description}
        
        Existing Knowledge (Context):
        {context_text}
        
        Original Article Content:
        {old_content}
        
        Proposed New Content:
        {new_content}
        
        Task: Analyze the proposed changes for consistency errors.
        Check for:
        1. Contradictions with the World Description.
        2. Contradictions with Existing Knowledge (Context).
        3. Internal logic errors or timeline anachronisms introduced by the change.
        
        Ignore minor stylistic changes or grammar fixes. Focus on factual/lore consistency.
        
        Output a JSON object with the following structure:
        {{
            "is_valid": boolean, // true if no major consistency errors found
            "issues": ["issue 1", "issue 2"] // list of specific consistency issues found, empty if valid
        }}
        """

        # 4. Call LLM
        try:
            result = await llm_service.generate_json(
                prompt,
                model=config.llm_model,
                schema=ValidationOutput,
                system_prompt="You are a strict consistency validator.",
            )
            return result.is_valid, result.issues
        except Exception as e:
            print(f"Validation failed: {e}")
            # If validation fails technically, we warn but allow (or fail safe)
            return True, ["Validation service unavailable. Proceed with caution."]


validator_service = ValidatorService()
