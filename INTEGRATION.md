# Integrate this completion pack

Copy `app/history.py` and `app/evaluation.py` into your existing `app/` folder. Copy the two test files into `tests/`. Copy `Dockerfile`, `compose.yaml`, `.dockerignore`, and `.env.example` into the project root.

## Add history to existing `app/main.py`

Add this import with the existing imports:
```python
from app.history import init_history_db, save_run, list_runs, get_run
```

After your `app = FastAPI(...)` declaration, add:
```python
@app.on_event("startup")
def startup_history():
    init_history_db()
```

In the existing successful `/research` handler, after the call to `run_research(...)` and before returning the result, add:
```python
save_run(result)
```
Use the raw dictionary returned by `run_research` before converting it to a Pydantic response model.

Add these endpoints:
```python
@app.get("/runs")
def research_runs(limit: int = 20):
    return {"runs": list_runs(limit)}

@app.get("/runs/{run_id}")
def research_run_detail(run_id: str):
    from fastapi import HTTPException
    result = get_run(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Research run not found")
    return result
```

Keep your existing `/`, `/health`, `/research`, and `/documents` routes. Do not replace `main.py` wholesale.

## Windows CMD setup and tests
```cmd
copy .env.example .env
.venv\Scripts\python.exe -m pytest -q
```
Edit `.env` locally and add your OpenAI API key. Add `TAVILY_API_KEY` if you want web search.

## Run locally
API:
```cmd
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
UI in a second terminal:
```cmd
.venv\Scripts\python.exe -m streamlit run frontend\streamlit_app.py
```

## Docker
With Docker Desktop running and `.env` configured:
```cmd
docker compose up --build
```
API docs: http://localhost:8000/docs ; UI: http://localhost:8501

SQLite history is local persistence, not PostgreSQL. The evaluation helpers do not claim a measured RAG score until you provide labelled relevant document IDs. Source-marker matching is only a heuristic, not proof of factual correctness.
