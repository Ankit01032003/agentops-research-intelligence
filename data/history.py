"""SQLite persistence for completed research runs."""
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("HISTORY_DB_PATH", "data/research_history.sqlite3"))

def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_history_db():
    with _connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS research_runs (
            run_id TEXT PRIMARY KEY, question TEXT NOT NULL, status TEXT NOT NULL,
            created_at TEXT NOT NULL, result_json TEXT NOT NULL)""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_created_at ON research_runs(created_at DESC)")

def save_run(result: dict[str, Any]):
    init_history_db()
    run_id = str(result.get("run_id", "")).strip()
    question = str(result.get("question", "")).strip()
    if not run_id or not question:
        raise ValueError("Research result must contain run_id and question.")
    created_at = str(result.get("created_at") or datetime.now(timezone.utc).isoformat())
    payload = json.dumps(result, ensure_ascii=False, default=str)
    with _connect() as conn:
        conn.execute("""INSERT INTO research_runs(run_id, question, status, created_at, result_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET question=excluded.question,
            status=excluded.status, result_json=excluded.result_json""",
            (run_id, question, str(result.get("status", "completed")), created_at, payload))

def list_runs(limit: int = 20):
    init_history_db()
    limit = max(1, min(int(limit), 100))
    with _connect() as conn:
        rows = conn.execute("""SELECT run_id, question, status, created_at
            FROM research_runs ORDER BY created_at DESC LIMIT ?""", (limit,)).fetchall()
    return [dict(row) for row in rows]

def get_run(run_id: str):
    init_history_db()
    with _connect() as conn:
        row = conn.execute("SELECT result_json FROM research_runs WHERE run_id = ?", (run_id,)).fetchone()
    return json.loads(row["result_json"]) if row else None
