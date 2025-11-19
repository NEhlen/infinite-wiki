# Infinite Wiki

![Infinite Wiki Banner](assets/banner_multiverse.png)

Infinite Wiki is an AI-powered world-building tool that automatically generates consistent wiki articles, timelines, and knowledge graphs for your custom worlds.

## Features

- **Multi-World Support**: Create and manage multiple distinct worlds.
- **Magic Config**: Generate a full world configuration (system prompts, seed article) from a single text description.
- **Auto-Generation**:
    - **Articles**: Two-stage generation (Plan -> Write) using RAG and Knowledge Graph context.
    - **Images**: AI-generated images with captions, saved locally.
    - **Links**: Automatic detection and linking of entities within articles.
- **Visualizers**: Interactive Knowledge Graph and Timeline views.
- **Consistency**: Uses ChromaDB (Vector Store) and NetworkX (Graph) to maintain consistency across generated content.

## API Providers & Costs

Infinite Wiki is designed to work with **any OpenAI-compatible API**. This includes:
- **OpenAI** (GPT-4, GPT-3.5)
- **xAI** (Grok)
- **Google Gemini** (via OpenAI compatibility)
- **Local Models** (via LM Studio, Ollama, etc.)

**Important**: You must provide your own API key. 
- **Budgeting Tip**: Providers like OpenAI and xAI allow you to set **prepaid budgets** or usage limits. We highly recommend setting a small limit (e.g., $5-10) when starting out to prevent accidental overspending while generating large worlds.
From experience, you should expect to pay around $1-2 per 10 articles generated.

## Prerequisites

- Python 3.12+
- OpenAI API Key (or compatible provider like Grok, etc.)

## Installation (Local)

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/infinite-wiki.git
    cd infinite-wiki
    ```

2.  **Create a virtual environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**:
    Create a `.env` file in the root directory:
    ```env
    OPENAI_API_KEY=your_api_key_here
    # Optional: Custom Base URL (e.g. for Grok or Local LLMs)
    # OPENAI_BASE_URL=https://api.openai.com/v1
    ```

5.  **Run the application**:
    ```bash
    uvicorn app.main:app --reload
    ```

6.  **Access the Wiki**:
    Open your browser and navigate to `http://127.0.0.1:8000`.

## Configuration

The application is configured via environment variables or a `.env` file. See `.env.example` for a full list of options.

### Common Options

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Required API Key for the LLM provider. | None |
| `OPENAI_BASE_URL` | Custom API Endpoint (e.g., for Grok, LocalAI). | Provider Default |
| `AI_PROVIDER` | `openai`, `xai`, `gemini`, `custom`, or `auto`. | `auto` |
| `LLM_MODEL` | Specific model to use (e.g., `gpt-4`, `grok-beta`). | Provider Default |

## Installation (Docker)

The Docker image does **not** contain your API keys. You must pass them at runtime.

1.  **Build the image** (or pull from registry):
    ```bash
    docker build -t infinite-wiki .
    ```

2.  **Run the container**:
    ```bash
    docker run -d -p 8000:8000 \
      -e OPENAI_API_KEY="your_actual_api_key" \
      -v $(pwd)/worlds:/app/worlds \
      infinite-wiki
    ```
    *   `-e OPENAI_API_KEY=...`: Injects your API key into the container.
    *   `-v $(pwd)/worlds:/app/worlds`: Mounts a local directory to persist your world data.

    **Using a .env file with Docker:**
    You can also pass your local `.env` file directly:
    ```bash
    docker run -d -p 8000:8000 \
      --env-file .env \
      -v $(pwd)/worlds:/app/worlds \
      infinite-wiki
    ```

## Usage

1.  **Create a World**:
    - Open `http://127.0.0.1:8000` in your browser.
    - Click "Create New World".
    - Use the **Magic Config** section: Enter a description (e.g., "A cyberpunk city run by cats") and click "Auto-Fill".
    - Click "Create World".

2.  **Explore & Generate**:
    - You will be redirected to the seed article.
    - Click on red links (missing articles) to auto-generate them.
    - Use the **Visualizers** link in the header to see the Timeline and Graph.

## License

MIT
