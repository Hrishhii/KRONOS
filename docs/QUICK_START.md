# ⚡ KRONOS Quick Start Guide

## Project Reorganization Overview

The KRONOS project has been reorganized to isolate the backend logic and centralize logging, resulting in a cleaner and more maintainable root directory. All backend-related files and subdirectories are now located in the `backend/` directory.

### 📁 New Directory Structure

```text
KRONOS/
├── backend/                    ← FastAPI + Multi-Agent Logic
│   ├── domain_connectors/      ← API Providers
│   ├── scripts/                ← Maintenance & Utility Scripts
│   ├── tests/                  ← Organized test files
│   ├── main.py                 ← FastAPI server
│   ├── graph.py                ← Core LangGraph
│   ├── config.py               ← Configuration
│   └── schemas.py              ← Data Schemas
├── frontend/                   ← React + Vite modern frontend
│   ├── src/
│   ├── dist/
│   └── package.json
├── logs/                       ← Centralized system logs
├── start-dev.bat               ← Quick start script
└── .gitignore                  ← Clean Git tracking
```

## How to Use It

### Quick Start (Development)

```bash
# Terminal 1: Start Backend (from root)
.\venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Start Frontend (separate terminal)
cd frontend
npm run dev

# Then open: http://localhost:5173
```

### Or Use the Quick Start Script
```bash
# One command starts both servers in separate windows
./start-dev.bat
```

### Production Mode (Single Server)
```bash
# Your backend serves the built React app
uvicorn backend.main:app --port 8000

# Visit: http://localhost:8000
```

## Testing Before You Ship

1. **Test Backend Alone**
   ```bash
   uvicorn backend.main:app --reload --port 8000
   curl http://localhost:8000/health
   ```

2. **Test Frontend Dev Server**
   ```bash
   cd frontend && npm run dev
   # Should start at localhost:5173
   ```

3. **Full Integration Test**
   - Start both servers
   - Enter a query: "Tell me about geopolitical tensions"
   - Verify response loads in ~5-6 seconds

4. **Production Build Test**
   ```bash
   cd frontend && npm run build
   uvicorn backend.main:app --port 8000
   # Visit http://localhost:8000
   # Should see same UI
   ```

## Key Changes
- **Backend Entry Point**: Changed from `main:app` to `backend.main:app`.
- **Static Files**: Backend now looks for the frontend build in `../frontend/dist`.
- **Logs**: System logs are now written to `logs/graph_debug.log`.
