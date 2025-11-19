from sqlmodel import SQLModel, create_engine, Session
from app.core.world import world_manager

# Cache engines to avoid recreating them
_engines = {}

def get_engine(world_name: str):
    if world_name not in _engines:
        paths = world_manager.get_paths(world_name)
        connect_args = {"check_same_thread": False}
        _engines[world_name] = create_engine(paths["db"], connect_args=connect_args)
    return _engines[world_name]

def create_db_and_tables(world_name: str):
    engine = get_engine(world_name)
    SQLModel.metadata.create_all(engine)

def get_session(world_name: str):
    engine = get_engine(world_name)
    with Session(engine) as session:
        yield session
