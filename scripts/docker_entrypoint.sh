#!/bin/bash
set -e

# Enforce internal path for Docker
export WORLD_DATA_DIR=/app/worlds

# Run the command passed to docker run (or the default CMD)
exec "$@"
