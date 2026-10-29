import app.history as history

def test_save_list_and_get_run(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "DB_PATH", tmp_path / "history.sqlite3")
    item = {"run_id": "run-test-1", "question": "How do agents use tools?",
            "status": "completed", "report": "Example report", "sources": []}
    history.save_run(item)
    assert history.get_run("run-test-1")["report"] == "Example report"
    listed = history.list_runs()
    assert listed[0]["run_id"] == "run-test-1"
    assert listed[0]["question"] == item["question"]

def test_missing_run_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "DB_PATH", tmp_path / "history.sqlite3")
    assert history.get_run("missing") is None
