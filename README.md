# ⚡ KRONOS | Neural Intelligence Mesh

> **Strategic Intelligence Operations & Predictive Ontology Convergence System**

![KRONOS Dashboard](docs/images/Screenshot%202026-03-31%20223533.png)

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.15+-blue?style=for-the-badge&logo=neo4j&logoColor=white)](https://neo4j.com/)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-6F3AF5?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)

KRONOS is a multi-agent intelligence platform for strategic forecasting and real-time geopolitical monitoring. It synthesizes data from 11+ global intelligence streams into an interactive **Knowledge Graph** powered by Neo4j and LangGraph, with interactive visualization dashboard.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Core Features](#core-features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the System](#running-the-system)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)
- [Pushing to GitHub](#pushing-to-github)

---

## 🎯 Overview

KRONOS is engineered to:
- Process complex geopolitical queries using multi-agent AI systems
- Extract entities and relationships from intelligence sources
- Build and maintain a normalized knowledge graph
- Visualize relationships in real-time with an interactive dashboard
- Generate predictive briefings with dependency tracking

Key differentiator: **Zero-clutter ontology** — only connected nodes are persisted; orphaned entities are filtered out automatically.

---

## 🛰️ Architecture

### System Pipeline

```
User Query
    ↓
Neural Router (Agent 0)
    ↓
Parallel Domain Agents
    ├─→ Geopolitics Agent (Agent 1)
    ├─→ Climate Agent (Agent 2)
    ├─→ Economics Agent (Agent 3)
    └─→ Technology Agent (Agent 4)
    ↓
Support Context Streams
    ├─→ Tavily contextual knowledge
    └─→ Neo4j Knowledge Graph context fetch
    ↓
Cross-domain synthesis via LLM (Groq + LLaMA 3.1)
    ↓
Chief Editor Agent (final briefing)
    ↓
Neo4j persist + API response
```

### Component Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | FastAPI + Python 3.10+ | Multi-agent orchestration, API endpoints |
| **LLMs (Inference Engine)** | Groq + LLaMA 3.1 / 3.3 | Ultra-fast inference for core routing and analysis |
| **Knowledge Graph** | Neo4j | Entity/relationship persistence |
| **Agent Framework** | LangGraph | Agentic workflows and routing |
| **Frontend** | React 18 + Vite | Interactive graph visualization |
| **Canvas Engine** | React Canvas 2D | Custom physics-based graph rendering |

---

## 🌐 Data Sources & APIs

KRONOS ingests live and historical metrics from the following external APIs.

*Note: The AI operations are handled securely via [Groq](https://console.groq.com/) using LLaMA models (specifically LLaMA 3.1 and 3.3), acting as the central intelligence engine rather than a raw data feed.*

| Domain / Engine | API Integrations & Links |
|-----------------|--------------------------|
| **Economics** | [FRED (Federal Reserve Economic Data)](https://fred.stlouisfed.org/docs/api/fred/) <br> [yfinance (Yahoo Finance)](https://pypi.org/project/yfinance/) |
| **Geopolitics & News** | [Google News RSS](https://news.google.com/rss) <br> [NewsAPI](https://newsapi.org/) |
| **Climate & Weather** | [OpenWeatherMap API](https://openweathermap.org/api) |
| **Aerospace & Space** | [NASA API (EONET)](https://api.nasa.gov/) |
| **Transportation** | [OpenSky Network API](https://openskynetwork.github.io/opensky-api/) (Flights) |
| **World Base Context** | [Tavily API](https://tavily.com/) *(Search and Guidance)* |

---

## 💎 Core Features

### 1. **Multi-Domain Intelligence Agents**
- Parallel execution of 4 core domain agents (Geopolitics, Climate, Economics, Technology)
- Augmented by 2 context streams (Tavily guidance + Neo4j knowledge graph context)
- Support from intelligence data feeds APIs including **Google News RSS**, **FRED**, **NewsAPI**, **OpenWeatherMap**, **NASA API**, **OpenSky**, **yfinance**, and **Tavily**
- 2-degree graph contextual neighborhood fetching for precision intelligence

### 2. **Intelligent Ontology Management**
- Automatic entity normalization (merges aliases)
- Strict connectivity validation (orphaned nodes removed)
- Relationship type classification and validation
- Whitelist-based entity filtering

### 3. **Interactive Knowledge Graph Visualization**
- Physics-based node layout with force-directed simulation
- Hover tooltips showing entity relationships
- Color-coded node types (Country, Asset, Leader, Organization, etc.)
- One-click node navigation
- Drag-to-pan, scroll-to-zoom controls

### 4. **Real-Time Updates**
- Async background task processing
- 60-second polling interval for graph updates
- Seamless frontend refresh without page reload

---

## 📦 Prerequisites

Before installation, ensure you have:

- **Python 3.10+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **Neo4j Desktop** ([Download](https://neo4j.com/download/)) with local instance running
- **API Keys** for: Groq, NewsAPI, Tavily, and optionally FRED, GDELT

---

## ⚙️ Installation

### 1. Clone Repository
```bash
git clone https://github.com/YOUR-USERNAME/KRONOS.git
cd KRONOS
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

#### Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

---

## 🔑 Configuration

### 1. Environment Variables

Copy the `.env.example` file to create a `.env` file in the project root:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Open the newly created `.env` file and replace the placeholders with your actual keys. The file should look like this:

```env
# Add your API keys here
FRED_API_KEY=your_fredapi_key_here
NEWSAPI_KEY=your_newsapi_key_here
OPENWEATHERMAP_API_KEY=your_openweathermapapi_key_here
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
NASA_API_KEY=your_nasa_api_key_here

# Free APIs for flights and ships (no API keys needed)
OPENSKY_API_ENABLED=true
NEO4J_PASSWORD=your_neo4j_password_here
```

### 2. Neo4j Setup

1. Open **Neo4j Desktop**
2. Create a new local DBMS named `kronos`
3. Start the instance
4. Set a password (default: `neo4j`)
5. Verify connection: `bolt://localhost:7687`
6. Install APOC plugin (required for graph operations):
   - In Neo4j Desktop, go to Plugins
   - Install APOC
   - Restart the database

---

## 🚀 Running the System



#### Terminal 1 - Backend Server
```bash
# Activate venv first
.\venv\Scripts\Activate.ps1

# Start FastAPI server (reloads on code changes)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

#### Terminal 2 - Frontend Server
```bash
cd frontend
npm run dev
```

Frontend will be available at: `http://localhost:5173`


---

## 📁 Project Structure

```
KRONOS/
├── backend/
│   ├── main.py                      # FastAPI application & routes
│   ├── config.py                    # Configuration settings
│   ├── graph.py                     # Graph processing logic
│   ├── graph_engine_connector.py    # Neo4j connection handler
│   ├── graph_engine_updater.py      # Async ontology extraction
│   ├── graph_engine_schema.py       # Data validation schemas
│   ├── schemas.py                   # Pydantic models
│   ├── domain_connectors/           # Domain-specific agent modules
│   │   ├── geopolitics.py
│   │   ├── economics.py
│   │   ├── technology.py
│   │   ├── climate.py
│   │   ├── flights.py
│   │   ├── ships.py
│   │   └── ...
│   ├── scripts/                     # Utility scripts
│   │   ├── seed_graph.py
│   │   ├── test_graph_context.py
│   │   └── ...
│   ├── tests/                       # Unit tests
│   └── __pycache__/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── KnowledgeGraph.jsx   # Main visualization component
│   │   │   ├── Dashboard.jsx
│   │   │   ├── BriefingDisplay.jsx
│   │   │   ├── WorldMap.jsx
│   │   │   └── ...
│   │   ├── hooks/
│   │   │   └── useApi.js            # API communication hook
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── eslint.config.js
├── docs/
│   ├── DEVELOPMENT.md               # Development guide
│   ├── QUICK_START.md               # Quick start guide
│   └── images/
├── logs/                            # Application logs
├── requirements.txt                 # Python dependencies
├── package.json                     # Project metadata
├── README.md                        # This file
└── .gitignore                       # Git ignore rules
```

---

## 📡 API Endpoints

### Query Processing
- **POST** `/api/v1/query` - Submit intelligence query
- **GET** `/api/v1/query/{query_id}` - Get query status

### Graph Data
- **GET** `/api/v1/graph/data` - Get full knowledge graph
- **GET** `/api/v1/graph/node/{node_id}` - Get node details
- **GET** `/api/v1/graph/relationships/{node_id}` - Get node relationships

### System Health
- **GET** `/api/v1/health` - System status
- **GET** `/api/v1/stats` - Graph statistics

> Full API documentation available at `http://localhost:8000/docs` (Swagger UI)

---

## 🐛 Troubleshooting

### Issue: Neo4j Connection Failed
**Solution:**
1. Verify Neo4j Desktop is running
2. Check password in `.env` matches Neo4j instance
3. Test connection: `cypher-shell -a bolt://localhost:7687 -u neo4j`

### Issue: API Keys Invalid
**Solution:**
1. Verify all API keys in `.env` are correct
2. Check API key permissions/quotas
3. Review backend logs for specific error messages

### Issue: Frontend Cannot Connect to Backend
**Solution:**
1. Ensure backend is running on port 8000
2. Check `ALLOWED_ORIGINS` in `.env` includes frontend URL
3. Verify firewall isn't blocking localhost connections

### Issue: Graph Visualization Not Updating
**Solution:**
1. Check browser console for errors (F12)
2. Verify Neo4j has data via Neo4j Browser
3. Check polling interval hasn't been disabled
4. Restart frontend server: `npm run dev`

---

## 💬 Example Queries

Interact with KRONOS using natural language queries:
- `Investigate the export of crude oil from Russia to Cuba`
- `Assess the impact of Fed interest rates on semiconductor technology`
- `Track US sanctions on the Iranian energy sector`
- `Monitor military alignments in the South China Sea`

---

## 📚 Additional Documentation

- [Development Guide](./docs/DEVELOPMENT.md) - Contributing guidelines and architecture details
- [Quick Start Guide](./docs/QUICK_START.md) - First-time user walkthrough

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📧 Support

For issues, questions, or suggestions:
- Open an [Issue](https://github.com/YOUR-USERNAME/KRONOS/issues)
- Check existing documentation in `/docs`

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](./LICENSE) file for details.

---

**KRONOS** — Building the future of strategic intelligence. 🚀
