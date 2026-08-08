# AGENTS.md — ENIGMA Project Commands

## Project Structure
- **Backend**: `enigma-backend/` — FastAPI + SQLAlchemy (async, Neon PostgreSQL) + NVIDIA NIM LLM
- **Frontend**: `enigma-frontend/` — vanilla ES-module JS + Tailwind CSS (modular; `index.html` has an inline fallback)

## Backend

### Activate Virtual Environment
```powershell
cd enigma-backend
..\.venv\Scripts\Activate.ps1   # or ..\.venv\Scripts\activate.bat
```

### Run the API Server (dev)
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run a Syntax / Import Check
```powershell
python -c "from app.main import app; print('OK')"
```

### Run Tests
No formal test framework is configured yet.  Run the smoke-test script instead:
```powershell
python test_engine.py
```

### Lint
No linter is configured.  Use Python's built-in compile check:
```powershell
python -m py_compile enigma-backend/app/**/*.py
```

## Frontend
No build step — served as static files (e.g. via `python -m http.server 8080`
from `enigma-frontend/`).

## Environment
- Python 3.11
- Backend deps: `requirements.txt`
