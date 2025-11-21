# Infinite Wiki

![Infinite Wiki Banner](assets/banner_multiverse.png)

Infinite Wiki is an AI-powered world-building tool that automatically generates consistent wiki articles, timelines, and knowledge graphs for your custom worlds.

## Live Demo
Check out the static, read-only demo of generated worlds here:
[**Infinite Wiki Demo**](https://nehlen.github.io/infinite-wiki/)

*Note: The demo is a static export. Article generation, editing, and dynamic features are disabled as they require a running backend and API key.*

## Features

### 1. Multi-World Management
Create and manage multiple distinct worlds.
<details>
<summary>View Home Screen</summary>

![Home View](assets/home_view.png)
</details>

### 2. Magic Config & World Dashboard
Generate a full world configuration from a single text description.
<details>
<summary>View World Dashboard</summary>

![World Dashboard](assets/world_view.png)
</details>

### 3. Auto-Generated Articles
Two-stage generation (Plan -> Write) using RAG and Knowledge Graph context.
<details>
<summary>View Article Page</summary>

![Article View](assets/article_view.png)
![Article View](assets/article_view_2.png)
</details>

### 4. Interactive Visualizers
Explore your world with interactive Knowledge Graph and Timeline views.
<details>
<summary>View Graph Visualization</summary>

![Graph View](assets/graph_view.png)
</details>

### 5. Human-AI Collaboration
- **Editable Articles**: Edit any article with AI validation.
<details>
<summary>View Edit Interface</summary>

![Edit Interface](assets/edit_interface.png)
</details>

- **Custom Creation**: Create articles with specific instructions.
<details>
<summary>View Custom Creation Interface</summary>

![Custom Creation Interface](assets/custom_creation_interface.png)
</details>

- **Selected Text Generation**: Highlight text to generate new articles or expand on concepts, optional short description can be given to influence new article generation.
<details>
<summary>View Selected Text Feature</summary>

![Selected Text Generation](assets/selected_text_generation.png)
</details>


- **Deduplication**: Automatically detects and redirects duplicate entity requests.

## API Providers & Costs

Infinite Wiki is designed to work with **any OpenAI-compatible API**. This includes:
- **OpenAI** (GPT-4, GPT-3.5)
- **xAI** (Grok)
- **Google Gemini** (via OpenAI compatibility)
- **Local Models** (via LM Studio, Ollama, etc.)

**Important**: You must provide your own API key. 
- **Budgeting Tip**: Providers like OpenAI and xAI allow you to set **prepaid budgets** or usage limits. I highly recommend setting a small limit (e.g., $5-10) when starting out to prevent accidental overspending while generating large worlds.
From experience, you should expect to pay around $1-2 per 10 articles generated (if you use grok-4-1-fast-reasoning).

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

3.  **Advanced Features**:
    - **Custom Article Creation**: Go to the World Overview page and use the "Create New Article" form to provide a specific title and description/instructions.
    - **Edit & Validate**: Click "Edit" on any article. Make changes and click "Save". The AI will validate your changes against the world lore. You can fix issues or "Force Save" to override them.
    - **Deduplication**: If you try to generate an article that already exists under a different name (e.g., "The Captain" vs "Captain Sarah"), the system will automatically redirect you to the existing article and link them in the graph.

## Current Limitations

- Images are currently not validated, so characters and objects are not coherent between articles
- The Timeline Feature is buggy

## License

MIT
