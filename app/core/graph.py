import networkx as nx
import json
import os
from typing import List, Dict
from app.core.world import world_manager

class GraphService:
    def __init__(self):
        self._graphs = {}

    def get_graph(self, world_name: str) -> nx.Graph:
        if world_name not in self._graphs:
            self.load_graph(world_name)
        return self._graphs[world_name]

    def load_graph(self, world_name: str):
        path = world_manager.get_paths(world_name)["graph"]
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                self._graphs[world_name] = nx.node_link_graph(data)
        else:
            self._graphs[world_name] = nx.Graph()

    def save_graph(self, world_name: str):
        path = world_manager.get_paths(world_name)["graph"]
        graph = self.get_graph(world_name)
        data = nx.node_link_data(graph)
        with open(path, "w") as f:
            json.dump(data, f)

    def add_entity(self, world_name: str, name: str, type: str, attributes: Dict = None):
        graph = self.get_graph(world_name)
        if not graph.has_node(name):
            attrs = {"type": type}
            if attributes:
                attrs.update(attributes)
            graph.add_node(name, **attrs)
            self.save_graph(world_name)
        else:
            # Update existing if needed
            if attributes:
                for k, v in attributes.items():
                    graph.nodes[name][k] = v
                self.save_graph(world_name)

    def add_relationship(self, world_name: str, source: str, target: str, relation: str):
        graph = self.get_graph(world_name)
        graph.add_edge(source, target, relation=relation)
        self.save_graph(world_name)

    def get_neighbors(self, world_name: str, entity: str) -> List[str]:
        graph = self.get_graph(world_name)
        if graph.has_node(entity):
            return list(graph.neighbors(entity))
        return []
    
    def get_context_subgraph(self, world_name: str, entities: List[str], depth: int = 1) -> str:
        graph = self.get_graph(world_name)
        relevant_nodes = set(entities)
        for entity in entities:
            if graph.has_node(entity):
                neighbors = nx.single_source_shortest_path_length(graph, entity, cutoff=depth)
                relevant_nodes.update(neighbors.keys())
        
        subgraph = graph.subgraph(relevant_nodes)
        return str(nx.node_link_data(subgraph))

graph_service = GraphService()
