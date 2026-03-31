# ⚡ KRONOS Development Guide

## Neural Pipeline Development

The KRONOS project has been reorganized into a clean, professional structure to isolate backend intelligence from frontend tactical display.

### 🏛️ Backend Architecture (Python 3.10+)

The backend is a FastAPI application that orchestrates multi-agent intelligence streams. The logic is now centralized in the `backend/` directory.

#### Project Directory Structure

```text
KRONOS/
├── backend/                    # FastAPI + Multi-Agent Logic
│   ├── domain_connectors/      # API Integration Modules
│   ├── scripts/                # Utility & Maintenance Scripts
│   ├── tests/                  # Backend Test Suite
│   ├── main.py                 # FastAPI Gateway
│   ├── graph.py                # LangGraph Orchestration
│   ├── config.py               # Neural Settings
│   └── schemas.py              # Data Schemas
├── frontend/                   # React + Vite Tactical UI
├── logs/                       # System Intelligence Logs
└── start-dev.bat               # Automated Ignition
```

### 🛠️ Working with the Backend

To run the backend during development:
```bash
uvicorn backend.main:app --reload --port 8000
```

#### Core Components
- **`backend/main.py`**: The API gateway. It serves the REST API and the built frontend assets.
- **`backend/graph.py`**: Orchestrates the LangGraph multi-agent pipeline.
- **`backend/domain_connectors/`**: Individual modules for fetching data from external APIs (FRED, NewsAPI, GDELT, etc.).
- **`backend/config.py`**: Centralized Pydantic settings that pull from `.env`.

### 🧪 Running Maintenance Scripts

Scripts should be run as modules from the root directory:
```bash
# Check database connectivity
python -m backend.scripts.check_db

# Merge duplicate entities in Neo4j
python -m backend.scripts.merge_duplicates
```

### 🧠 Intelligence Pipeline

1. **Router Agent**: Analyzes the query and determines which domains to activate.
2. **Domain Agents**: Fetch specific data from their assigned APIs in parallel.
3. **Ontology Extractor**: Converts unstructured results into Cypher queries for Neo4j.
4. **Chief Editor Agent**: Synthesizes the final tactical briefing based on the Knowledge Graph.

## Logging & Debugging

Logs are now centralized in the root `logs/` directory.
- `logs/graph_debug.log`: Detailed trace of the multi-agent pipeline, extraction queries, and API responses.

## Deployment Tips

When deploying, ensure the following environment variables are set:
- `GROQ_API_KEY`: For LLM orchestration.
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`: For the tactical mesh.
- Various domain API keys (NEWSAPI_KEY, TAVILY_API_KEY, etc.).
