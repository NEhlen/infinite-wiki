import os
import sys
from unittest.mock import patch

# Add project root to path
sys.path.append(os.getcwd())

from app.config import Settings
from app.core.timeline import TimelineService
from app.core.world import WorldManager, WorldConfig


def verify_config_quotes():
    print("Verifying Config Quote Stripping...")
    # Simulate quoted env vars
    with patch.dict(os.environ, {"AI_PROVIDER": '"xai"', "LLM_MODEL": "'grok-beta'"}):
        settings = Settings()
        if settings.AI_PROVIDER == "xai" and settings.LLM_MODEL == "grok-beta":
            print("SUCCESS: Quotes stripped correctly.")
        else:
            print(
                f"FAILED: AI_PROVIDER='{settings.AI_PROVIDER}', LLM_MODEL='{settings.LLM_MODEL}'"
            )
            sys.exit(1)


def verify_timeline_logic():
    print("\nVerifying Timeline Logic...")
    world_name = "timeline_test_world"

    # Setup world
    manager = WorldManager()
    if os.path.exists(manager.get_world_path(world_name)):
        import shutil

        shutil.rmtree(manager.get_world_path(world_name))
    manager.create_world(WorldConfig(name=world_name))

    service = TimelineService()

    # Add event with new fields
    service.add_event(
        world_name,
        "The Great Awakening",
        year_numeric=2024.5,
        display_date="Stardate 4523.1",
        description="AI wakes up.",
    )

    # Verify retrieval
    events = service.get_context_events(world_name)
    if not events:
        print("FAILED: No events found.")
        sys.exit(1)

    event = events[0]
    print(f"Retrieved Event: {event}")

    if event["year_numeric"] == 2024.5 and event["display_date"] == "Stardate 4523.1":
        print("SUCCESS: Timeline event stored and retrieved correctly.")
    else:
        print("FAILED: Data mismatch.")
        sys.exit(1)

    # Cleanup
    import shutil

    shutil.rmtree(manager.get_world_path(world_name))


if __name__ == "__main__":
    verify_config_quotes()
    verify_timeline_logic()
