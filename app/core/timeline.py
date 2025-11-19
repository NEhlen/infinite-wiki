from typing import List, Dict, Optional
from app.core.graph import graph_service

class TimelineService:
    def add_event(self, world_name: str, name: str, year: str, description: str):
        attributes = {"year": year, "description": description}
        graph_service.add_entity(world_name, name, "Event", attributes)

    def get_context_events(self, world_name: str, year: str, window: int = 50) -> List[Dict]:
        # This is a bit tricky with just a graph. 
        # For now, let's just return a few events that are close in the graph or just all events if small.
        # A proper implementation would need a database query or iterating all nodes.
        
        events = []
        graph = graph_service.get_graph(world_name)
        for node, data in graph.nodes(data=True):
            if data.get("type") == "Event" and "year" in data:
                events.append({"name": node, "year": data["year"], "description": data.get("description", "")})
        
        # Sort by year (assuming year is sortable string or int)
        try:
            events.sort(key=lambda x: int(x["year"]) if x["year"].isdigit() else 9999)
        except:
            pass
            
        return events

    def get_events_by_year(self, world_name: str, year: str) -> List[Dict]:
        """Get all events occurring in a specific year."""
        events = []
        graph = graph_service.get_graph(world_name)
        for node, data in graph.nodes(data=True):
            if data.get("type") == "Event" and str(data.get("year")) == str(year):
                events.append({"name": node, "year": data["year"], "description": data.get("description", "")})
        return events

    def get_nearby_events(self, world_name: str, target_year: str, range_years: int = 10) -> List[Dict]:
        """Get events within +/- range_years of the target year."""
        events = []
        try:
            target = int(target_year)
        except ValueError:
            return [] # Invalid year format

        graph = graph_service.get_graph(world_name)
        for node, data in graph.nodes(data=True):
            if data.get("type") == "Event" and "year" in data:
                try:
                    event_year = int(data["year"])
                    if abs(event_year - target) <= range_years:
                        events.append({"name": node, "year": data["year"], "description": data.get("description", "")})
                except ValueError:
                    continue # Skip events with non-integer years
        
        # Sort by year
        events.sort(key=lambda x: int(x["year"]))
        return events

timeline_service = TimelineService()
