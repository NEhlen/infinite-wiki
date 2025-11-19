import chromadb
from chromadb.config import Settings
from typing import List
from app.core.world import world_manager

class RAGService:
    def __init__(self):
        self._clients = {}

    def get_client(self, world_name: str):
        if world_name not in self._clients:
            path = world_manager.get_paths(world_name)["chroma"]
            self._clients[world_name] = chromadb.PersistentClient(path=path)
        return self._clients[world_name]

    def get_collection(self, world_name: str):
        client = self.get_client(world_name)
        return client.get_or_create_collection(name="wiki_articles")

    def add_article(self, world_name: str, title: str, content: str, article_id: int):
        collection = self.get_collection(world_name)
        collection.add(
            documents=[content],
            metadatas=[{"title": title, "id": article_id}],
            ids=[str(article_id)]
        )

    def query_context(self, world_name: str, query: str, n_results: int = 3) -> List[str]:
        collection = self.get_collection(world_name)
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        if results["documents"]:
            return results["documents"][0]
        return []

rag_service = RAGService()
