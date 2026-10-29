
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_short_question_is_rejected():
    response = client.post(
        "/research",
        json={"question": "Hi"},
    )

    assert response.status_code == 422


def test_invalid_document_type_is_rejected():
    response = client.post(
        "/documents",
        files={
            "file": (
                "test.exe",
                b"not a document",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
