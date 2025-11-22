# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project definition
COPY pyproject.toml /app/

# Install dependencies
RUN uv pip install --system -r pyproject.toml

# Pre-download ChromaDB models
COPY ./scripts/download_models.py /app/scripts/download_models.py
RUN python /app/scripts/download_models.py

# Copy the the app directory into app and exclude the test files, static site, scripts and assets
# Copy the the app directory into app and exclude the test files, static site, scripts and assets
COPY ./app /app/app
COPY ./worlds /app/worlds
COPY ./scripts/docker_entrypoint.sh /app/scripts/docker_entrypoint.sh

# Make entrypoint executable
RUN chmod +x /app/scripts/docker_entrypoint.sh

# Expose port 8000
EXPOSE 8000

# Define environment variable for persistence (default, enforced by entrypoint)
ENV WORLD_DATA_DIR=/app/worlds

# Create a volume for persistent data
VOLUME /app/worlds

# Set entrypoint
ENTRYPOINT ["/app/scripts/docker_entrypoint.sh"]

# Run uvicorn when the container launches
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
