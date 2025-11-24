import re
from app.core.graph import graph_service


class LinkerService:
    def autolink_content(self, world_name: str, content: str, session) -> str:
        """
        Scans the content and replaces occurrences of known entity names with Markdown links.
        """
        graph = graph_service.get_graph(world_name)
        # Get all entity names
        entities = list(graph.nodes())

        # Sort by length descending to handle substrings correctly (e.g. "Great War" before "Great")
        entities.sort(key=len, reverse=True)

        # Create a map of entity lower case to original case for case-insensitive matching if desired,
        # but for now let's stick to exact match or simple case insensitive.
        # To avoid linking inside existing links (e.g. [Some Entity](...)), this is complex with regex.
        # A simple approach:
        # 1. Split by existing markdown links to protect them?
        # 2. Or just use a negative lookahead/lookbehind?

        # Let's try a simpler approach first:
        # We iterate through entities and replace them if they are NOT already part of a link.
        # This is hard to do perfectly without a parser.

        # Alternative: We trust the LLM to link some, and we only link what's missing?
        # Or we just do a blind replace and hope for the best?
        # "Blind replace" breaks if we replace "Entity" inside "[Entity](...)" -> "[[Entity](...)](...)"

        # Better approach:
        # Tokenize the text into "text" and "link" chunks. Only process "text" chunks.
        # Since we don't have a full markdown parser, let's use a simplified regex for existing links.

        # Regex to find markdown links: \[.*?\]\(.*?\)
        # We will split the content by this regex.

        link_pattern = re.compile(r"(\[.*?\]\(.*?\))")
        parts = link_pattern.split(content)

        # Now 'parts' contains alternating [text, link, text, link, ...]
        # We only process the even indices (text).

        processed_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 0:  # It's text
                # Apply linking
                processed_parts.append(
                    self._link_text_chunk(part, entities, world_name, session)
                )
            else:  # It's a link, keep as is
                processed_parts.append(part)

        return "".join(processed_parts)

    def _link_text_chunk(
        self, text: str, entities: list, world_name: str, session
    ) -> str:
        # We need to be careful not to double link.
        # And we want to match whole words?
        # Let's use regex with word boundaries \b

        # Optimization: Only check entities that are actually in the text?
        # For 500 entities, checking all might be okay.

        # Construct a massive regex? Or iterate?
        # Massive regex is faster usually.
        # Pattern: \b(Entity1|Entity2|...)\b
        # We need to escape entities.

        if not entities:
            return text

        # Filter entities that are actually in the text to keep regex small
        present_entities = [e for e in entities if e in text]  # Simple check
        if not present_entities:
            return text

        present_entities.sort(key=len, reverse=True)

        # Escape for regex
        escaped_entities = [re.escape(e) for e in present_entities]
        pattern_str = r"\b(" + "|".join(escaped_entities) + r")\b"
        pattern = re.compile(pattern_str)

        import urllib.parse
        from app.models.article import Article
        from sqlmodel import select

        # Cache existence checks for this chunk to avoid DB spam
        existence_cache = {}

        def replace_func(match):
            entity_name = match.group(1)

            if entity_name not in existence_cache:
                statement = select(Article).where(Article.title == entity_name)
                exists = session.exec(statement).first() is not None
                existence_cache[entity_name] = exists
                print(f"Linker Debug: '{entity_name}' exists? {exists}")

            encoded_name = urllib.parse.quote(entity_name)

            if existence_cache[entity_name]:
                return f"[{entity_name}](/world/{world_name}/wiki/{encoded_name})"
            else:
                print(f"Linker Debug: Creating RED LINK for '{entity_name}'")
                # Red link with class
                # We use HTML anchor because markdown doesn't support classes easily,
                # but our renderer might support raw HTML.
                # Assuming the markdown renderer allows HTML (common default).
                return f'<a href="/world/{world_name}/wiki/{encoded_name}" class="new-article" data-title="{entity_name}">{entity_name}</a>'

        return pattern.sub(replace_func, text)


linker_service = LinkerService()
