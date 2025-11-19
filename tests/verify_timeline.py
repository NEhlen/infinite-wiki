import sys
import os
import asyncio
import shutil
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.getcwd())

from app.main import app
from app.core.world import world_manager, WorldConfig
from app.core.timeline import timeline_service
from app.database import create_db_and_tables

client = TestClient(app)

def verify_timeline():
    print("Starting Timeline Verification...")
    
    world_name = "TestWorld_Timeline"
    
    # 1. Clean up
    world_path = world_manager.get_world_path(world_name)
    if os.path.exists(world_path):
        shutil.rmtree(world_path)
        
    # 2. Create World
    print(f"Creating world '{world_name}'...")
    config = WorldConfig(name=world_name)
    world_manager.create_world(config)
    create_db_and_tables(world_name)
    
    # 3. Add Test Events
    print("Adding test events...")
    timeline_service.add_event(world_name, "Event A", "100", "Event in year 100")
    timeline_service.add_event(world_name, "Event B", "100", "Another event in year 100")
    timeline_service.add_event(world_name, "Event C", "105", "Event in year 105")
    timeline_service.add_event(world_name, "Event D", "120", "Event in year 120")
    
    # 4. Test get_events_by_year
    print("Testing get_events_by_year(100)...")
    response = client.get(f"/api/world/{world_name}/timeline/year/100")
    assert response.status_code == 200
    events = response.json()
    print(f"Found {len(events)} events.")
    assert len(events) == 2
    assert any(e["name"] == "Event A" for e in events)
    assert any(e["name"] == "Event B" for e in events)
    print("get_events_by_year: SUCCESS")
    
    # 5. Test get_nearby_events
    print("Testing get_nearby_events(100, range=10)...")
    response = client.get(f"/api/world/{world_name}/timeline/nearby/100?range=10")
    assert response.status_code == 200
    events = response.json()
    print(f"Found {len(events)} events.")
    # Should include 100 (A, B) and 105 (C), but not 120 (D)
    assert len(events) == 3
    assert any(e["name"] == "Event C" for e in events)
    assert not any(e["name"] == "Event D" for e in events)
    print("get_nearby_events: SUCCESS")
    
    print("Timeline Verification Complete.")

if __name__ == "__main__":
    verify_timeline()
