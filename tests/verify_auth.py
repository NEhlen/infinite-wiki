import sys
import os
import base64
from fastapi.testclient import TestClient
from unittest.mock import patch

# Add project root to path
sys.path.append(os.getcwd())

from app.main import app
from app.config import get_settings

settings = get_settings()


def verify_auth():
    print("Starting Auth Verification...")

    client = TestClient(app)

    # 1. Test without Auth (should be allowed if env vars are not set, but we will mock them)
    print("Testing with NO credentials set (should pass as anonymous)...")
    # Mock settings to have None
    with (
        patch.object(settings, "AUTH_USERNAME", None),
        patch.object(settings, "AUTH_PASSWORD", None),
    ):
        response = client.get("/")
        if response.status_code == 200:
            print("Anonymous access allowed when no auth set: SUCCESS")
        else:
            print(f"Anonymous access failed: {response.status_code}")
            sys.exit(1)

    # 2. Test with Auth set
    print("Testing with credentials set...")
    with (
        patch.object(settings, "AUTH_USERNAME", "admin"),
        patch.object(settings, "AUTH_PASSWORD", "secret"),
    ):

        # 2a. No credentials provided
        response = client.get("/")
        if response.status_code == 401:
            print("Access denied without credentials: SUCCESS")
        else:
            print(
                f"Access allowed without credentials: FAILED ({response.status_code})"
            )
            sys.exit(1)

        # 2b. Wrong credentials
        response = client.get("/", auth=("admin", "wrong"))
        if response.status_code == 401:
            print("Access denied with wrong credentials: SUCCESS")
        else:
            print(
                f"Access allowed with wrong credentials: FAILED ({response.status_code})"
            )
            sys.exit(1)

        # 2c. Correct credentials
        response = client.get("/", auth=("admin", "secret"))
        if response.status_code == 200:
            print("Access allowed with correct credentials: SUCCESS")
        else:
            print(
                f"Access failed with correct credentials: FAILED ({response.status_code})"
            )
            sys.exit(1)

    print("Auth Verification Complete.")


if __name__ == "__main__":
    verify_auth()
