import networkx as nx
import json
import os
from typing import List, Dict

GRAPH_FILE = "wiki_graph.json"

class GraphService:
    def __init__(self):
        self.graph = nx.Graph()
        self.load_graph()

    def load_graph(self):
        if os.path.exists(GRAPH_FILE):
            with open(GRAPH_FILE, "r") as f:
                data = json.load(f)
                self.graph = nx.node_link_graph(data)

    def save_graph(self):
        data = nx.node_link_data(self.graph)
        with open(GRAPH_FILE, "w") as f:
            json.dump(data, f)

    def add_entity(self, name: str, type: str, attributes: Dict = None):
        if not self.graph.has_node(name):
            attrs = {"type": type}
            if attributes:
                attrs.update(attributes)
            self.graph.add_node(name, **attrs)
            self.save_graph()
        else:
            # Update existing if needed
            if attributes:
                for k, v in attributes.items():
                    self.graph.nodes[name][k] = v
                self.save_graph()

    def add_relationship(self, source: str, target: str, relation: str):
        self.graph.add_edge(source, target, relation=relation)
        self.save_graph()

    def get_neighbors(self, entity: str) -> List[str]:
        if self.graph.has_node(entity):
            return list(self.graph.neighbors(entity))
        return []
    
    def get_context_subgraph(self, entities: List[str], depth: int = 1) -> str:
        # Simple implementation: get neighbors of all entities
        relevant_nodes = set(entities)
        for entity in entities:
            if self.graph.has_node(entity):
                neighbors = nx.single_source_shortest_path_length(self.graph, entity, cutoff=depth)
                relevant_nodes.update(neighbors.keys())
        
        subgraph = self.graph.subgraph(relevant_nodes)
        return str(nx.node_link_data(subgraph))

graph_service = GraphService()
