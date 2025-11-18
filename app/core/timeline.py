from typing import List, Dict, Optional
from app.core.graph import graph_service

class TimelineService:
    def add_event(self, name: str, year: str, description: str):
        attributes = {"year": year, "description": description}
        graph_service.add_entity(name, "Event", attributes)

    def get_context_events(self, year: str, window: int = 50) -> List[Dict]:
        # This is a bit tricky with just a graph. 
        # For now, let's just return a few events that are close in the graph or just all events if small.
        # A proper implementation would need a database query or iterating all nodes.
        
        events = []
        for node, data in graph_service.graph.nodes(data=True):
            if data.get("type") == "Event" and "year" in data:
                events.append({"name": node, "year": data["year"], "description": data.get("description", "")})
        
        # Sort by year (assuming year is sortable string or int)
        try:
            events.sort(key=lambda x: int(x["year"]) if x["year"].isdigit() else 9999)
        except:
            pass
            
        return events

timeline_service = TimelineService()
