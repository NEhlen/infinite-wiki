import os
import shutil
from typing import List, Optional
from pydantic import BaseModel

class WorldConfig(BaseModel):
    name: str
    description: str = ""
    system_prompt_planner: str = "You are a creative world-building assistant."
    system_prompt_writer: str = "You are an encyclopedic writer."
    system_prompt_image: str = "You are an expert art director."
    llm_model: str = "grok-4-fast-reasoning-latest"
    image_gen_model: str = "grok-2-image-latest"

class WorldManager:
    def __init__(self, base_path: str = "worlds"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def get_world_path(self, world_name: str) -> str:
        return os.path.join(self.base_path, world_name)

    def create_world(self, config: WorldConfig):
        world_path = self.get_world_path(config.name)
        if os.path.exists(world_path):
            raise ValueError(f"World '{config.name}' already exists.")
        
        os.makedirs(world_path)
        
        # Save config
        with open(os.path.join(world_path, "config.json"), "w") as f:
            f.write(config.model_dump_json(indent=2))

    def list_worlds(self) -> List[str]:
        return [d for d in os.listdir(self.base_path) if os.path.isdir(os.path.join(self.base_path, d))]

    def get_config(self, world_name: str) -> WorldConfig:
        config_path = os.path.join(self.get_world_path(world_name), "config.json")
        if not os.path.exists(config_path):
            # Return default if no config exists (migration support)
            return WorldConfig(name=world_name)
        
        with open(config_path, "r") as f:
            return WorldConfig.model_validate_json(f.read())

    def get_paths(self, world_name: str):
        world_path = self.get_world_path(world_name)
        return {
            "db": f"sqlite:///{os.path.join(world_path, 'database.db')}",
            "graph": os.path.join(world_path, "wiki_graph.json"),
            "chroma": os.path.join(world_path, "chroma_db")
        }

world_manager = WorldManager()
