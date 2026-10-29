
# AgentOps Research Intelligence

An AI research application combining a LangGraph workflow, LLM-powered planning,
web search, document RAG, evidence review, and report generation.

## Features

- Research planning with an LLM
- Web search using Tavily
- PDF, TXT, and Markdown ingestion
- Semantic document retrieval with ChromaDB
- Evidence review and report generation
- FastAPI backend
- Streamlit user interface
- Pytest API tests

## Architecture

Streamlit UI -> FastAPI -> LangGraph workflow

The workflow coordinates:
1. Planner
2. Researcher
3. Evidence verifier
4. Report generator

The researcher combines web search results and retrieved document passages.

## Requirements

- Python 3.11 or 3.12
- OpenAI API key
- Tavily API key for live web search

## Setup

Create and activate a virtual environment, then install dependencies:

    python -m venv .venv
    python -m pip install -r requirements.txt

Create a `.env` file from `.env.example` and configure your keys.

## Run the API

    uvicorn app.main:app --reload

API documentation:

    http://127.0.0.1:8000/docs

## Run the frontend

Open a second terminal, activate the same virtual environment, and run:

    streamlit run frontend/streamlit_app.py

## Run tests

    pytest -q

## Limitations

- The workflow currently follows a fixed graph.
- Evidence review uses an LLM and is not a guarantee of truth.
- Document retrieval uses basic semantic search.
- The application is intended for local development, not unrestricted public use.
- Authentication, persistent run history, advanced evaluation, and production deployment
  are future improvements.

## Security

Keep API keys in `.env`. Never commit credentials or expose unrestricted tools to an LLM.
