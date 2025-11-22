from typing import List, Dict, Optional
from app.core.graph import graph_service


class TimelineService:
    def add_event(
        self,
        world_name: str,
        name: str,
        year_numeric: float,
        display_date: str,
        description: str,
    ):
        attributes = {
            "year_numeric": year_numeric,
            "display_date": display_date,
            "description": description,
        }
        graph_service.add_entity(world_name, name, "Event", attributes)

    def get_context_events(
        self, world_name: str, year: str = None, window: int = 50
    ) -> List[Dict]:
        events = []
        graph = graph_service.get_graph(world_name)
        for node, data in graph.nodes(data=True):
            if data.get("type") == "Event":
                # Handle both new and old formats
                year_numeric = data.get("year_numeric")
                display_date = data.get("display_date")

                # Migration/Fallback logic
                if year_numeric is None and "year" in data:
                    try:
                        year_numeric = float(data["year"])
                    except (ValueError, TypeError):
                        year_numeric = 99999  # Push to end if unparseable

                if display_date is None:
                    display_date = str(data.get("year", "Unknown Date"))

                if year_numeric is not None:
                    events.append(
                        {
                            "name": node,
                            "year_numeric": year_numeric,
                            "display_date": display_date,
                            "description": data.get("description", ""),
                        }
                    )

        # Sort by numeric year
        events.sort(key=lambda x: x["year_numeric"])
        return events

    def get_events_by_year(self, world_name: str, year: float) -> List[Dict]:
        """Get all events occurring in a specific year (numeric match)."""
        events = self.get_context_events(world_name)
        # Filter for events close to the target year (within 0.9 to catch floats in same integer year)
        return [e for e in events if abs(e["year_numeric"] - year) < 1.0]

    def get_nearby_events(
        self, world_name: str, target_year: float, range_years: int = 10
    ) -> List[Dict]:
        """Get events within +/- range_years of the target year."""
        events = self.get_context_events(world_name)
        return [
            e for e in events if abs(e["year_numeric"] - target_year) <= range_years
        ]


timeline_service = TimelineService()
