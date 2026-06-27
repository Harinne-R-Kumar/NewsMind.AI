# NewsMind AI

An autonomous personal intelligence agent that proactively gathers, personalizes, and delivers daily intelligence briefs based on your interests.

## Architecture

```
Scheduler → Supervisor Agent → Research Agent → MCP Tools → Editorial Agent → Memory Agent → Delivery Agent → Email
```

- **Research Agent** decides *what* to collect — never contains hardcoded URLs
- **MCP Tools** dynamically load sources from `backend/config/sources.yaml`
- **LangGraph** orchestrates the multi-agent workflow with conditional routing
- **ChromaDB** stores long-term memory (interests, reading history, feedback)

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React, Vite, Tailwind CSS, Axios |
| Backend | FastAPI, SQLAlchemy, SQLite |
| AI | LangGraph, LangChain, Ollama |
| MCP | Model Context Protocol (stdio server) |
| Memory | ChromaDB |
| Scheduler | APScheduler |
| Delivery | ReportLab (PDF), Gmail SMTP |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- [Ollama](https://ollama.ai) with `qwen2.5:7b` and `all-minilm:latest` models

### Backend

```bash
cd backend
cp .env.example .env          # Edit with your API keys
pip install -r requirements.txt
cd ..
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Database Initialization

Tables are created automatically on first startup via SQLAlchemy `init_db()`.

### Scheduler

The APScheduler starts automatically with the backend. It checks every minute for users whose delivery time matches (ist).

### MCP Server (standalone)

```bash
python -m backend.mcp.server
```

### Tests

```bash
pip install -r backend/requirements.txt
pytest tests/ -v
```

### Docker

```bash
cd docker
docker compose up --build
```

## Environment Variables

Copy `backend/.env.example` to `backend/.env`:

| Variable | Description | Required |
|----------|-------------|----------|
| `JWT_SECRET` | Secret for JWT signing | Yes (production) |
| `OLLAMA_URL` | Ollama API endpoint | Default: `http://localhost:11434` |
| `DEFAULT_LLM_MODEL` | LLM model name | Default: `qwen2.5:7b` |
| `EMBEDDING_MODEL` | Embedding model | Default: `all-minilm:latest` |
| `OPENWEATHER_API_KEY` | Weather data | Optional |
| `SMTP_HOST/USER/PASSWORD` | Email delivery | Optional |
| `CHROMA_DB_PATH` | ChromaDB storage | Default: `./chromadb_data` |

## Adding News Sources

Edit `backend/config/sources.yaml` — no Python changes required:

```yaml
- id: my_source
  name: "My Source"
  category: news
  type: rss_search
  template: "https://example.com/search?q={query}"
  priority: 5
  credibility: 0.8
  enabled: true
```

## Project Structure

```
newsmind/
├── backend/
│   ├── agents/          # LangGraph agent nodes
│   ├── api/             # FastAPI routers
│   ├── config/          # sources.yaml registry
│   ├── graph/           # LangGraph workflow
│   ├── mcp/             # MCP tools + server
│   ├── scheduler/       # APScheduler jobs
│   └── utils/           # Security, sanitization, logging
├── frontend/            # React dashboard
├── docker/              # Docker Compose configs
└── tests/               # Test suites
```

## Verification Checklist

- [ ] Backend starts at http://localhost:8000/api/health
- [ ] Frontend loads at http://localhost:5173
- [ ] Register → Login → Onboarding flow works
- [ ] Manual report generation from Dashboard
- [ ] PDF download with authentication
- [ ] Preferences CRUD (interests, sources, excluded topics)
- [ ] Schedule creation/deletion
- [ ] Ollama running for editorial summarization
