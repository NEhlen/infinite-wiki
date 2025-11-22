import os
import shutil
import sys
from unittest.mock import patch

# Add project root to path
sys.path.append(os.getcwd())

from app.core.world import WorldManager, WorldConfig


def verify_persistence():
    print("Starting Persistence Verification...")

    custom_dir = "test_custom_worlds"

    # Clean up if exists
    if os.path.exists(custom_dir):
        shutil.rmtree(custom_dir)

    # Mock environment variable
    print(f"Setting WORLD_DATA_DIR to '{custom_dir}'...")
    with patch.dict(os.environ, {"WORLD_DATA_DIR": custom_dir}):
        # Re-initialize manager to pick up env var
        manager = WorldManager()

        print(f"Manager base path: {manager.base_path}")

        if manager.base_path != custom_dir:
            print(
                f"FAILED: Manager did not pick up custom dir. Got: {manager.base_path}"
            )
            sys.exit(1)

        # Create a world
        print("Creating test world...")
        manager.create_world(WorldConfig(name="persistence_test"))

        # Check if it exists in the custom dir
        expected_path = os.path.join(custom_dir, "persistence_test")
        if os.path.exists(expected_path):
            print(f"SUCCESS: World created at {expected_path}")
        else:
            print(f"FAILED: World not found at {expected_path}")
            sys.exit(1)

    # Cleanup
    if os.path.exists(custom_dir):
        shutil.rmtree(custom_dir)

    print("Persistence Verification Complete.")


if __name__ == "__main__":
    verify_persistence()
