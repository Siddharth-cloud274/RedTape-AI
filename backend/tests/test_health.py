from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check_returns_200_and_valid_json():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "RedTape AI Backend"
    assert "version" in data


def test_health_check_cors_headers_allowed():
    headers = {"Origin": "http://localhost:5173"}
    response = client.get("/api/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_health_check_cors_headers_disallowed():
    headers = {"Origin": "http://untrusted-site.com"}
    response = client.get("/api/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") is None
