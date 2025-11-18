import chromadb
from chromadb.config import Settings
from typing import List

class RAGService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(name="wiki_articles")

    def add_article(self, title: str, content: str, article_id: int):
        self.collection.add(
            documents=[content],
            metadatas=[{"title": title, "id": article_id}],
            ids=[str(article_id)]
        )

    def query_context(self, query: str, n_results: int = 3) -> List[str]:
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        if results["documents"]:
            return results["documents"][0]
        return []

rag_service = RAGService()
