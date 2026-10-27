
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_healthy():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_health_check_returns_json():
    response = client.get("/health")

    assert response.headers["content-type"].startswith(
        "application/json"
    )
