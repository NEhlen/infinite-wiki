#!/bin/bash

echo "Infinite Wiki Launcher"
echo "======================"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add to path for this session
    if [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    elif [ -f "$HOME/.local/bin/env" ]; then # uv might install here on some systems
        source "$HOME/.local/bin/env"
    else
        # Fallback: try adding common paths
        export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
    fi
fi

echo ""
echo "Installing/Updating dependencies..."
uv sync

echo ""
echo "Starting Infinite Wiki..."
echo "Access the app at http://127.0.0.1:8000"
echo "Press Ctrl+C to stop."
echo ""

uv run uvicorn app.main:app --reload
