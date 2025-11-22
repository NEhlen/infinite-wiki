import os
import sys
import shutil

# Add project root to path
sys.path.append(os.getcwd())

from app.core.timeline import timeline_service
from app.core.graph import graph_service
from app.core.world import WorldManager, WorldConfig


def verify_backward_compatibility():
    print("Verifying Timeline Backward Compatibility...")
    world_name = "compat_test_world"

    # Setup world
    manager = WorldManager()
    if os.path.exists(manager.get_world_path(world_name)):
        shutil.rmtree(manager.get_world_path(world_name))
    manager.create_world(WorldConfig(name=world_name))

    # 1. Simulate "Old Style" Data (Directly inject into graph)
    print("Injecting legacy event (only 'year')...")
    graph_service.add_entity(
        world_name,
        "Legacy Event",
        "Event",
        {"year": "2023", "description": "Old event."},
    )

    # 2. Retrieve using new service
    print("Retrieving events...")
    events = timeline_service.get_context_events(world_name)

    if not events:
        print("FAILED: No events found.")
        sys.exit(1)

    event = events[0]
    print(f"Retrieved Event: {event}")

    # 3. Verify Migration Logic
    if event["year_numeric"] == 2023.0:
        print("SUCCESS: 'year' converted to 'year_numeric'.")
    else:
        print(f"FAILED: year_numeric mismatch. Got {event.get('year_numeric')}")
        sys.exit(1)

    if event["display_date"] == "2023":
        print("SUCCESS: 'year' used as 'display_date'.")
    else:
        print(f"FAILED: display_date mismatch. Got {event.get('display_date')}")
        sys.exit(1)

    # Cleanup
    shutil.rmtree(manager.get_world_path(world_name))


if __name__ == "__main__":
    verify_backward_compatibility()
