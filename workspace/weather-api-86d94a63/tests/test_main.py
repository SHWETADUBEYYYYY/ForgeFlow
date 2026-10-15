import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    import backend.main as main

    monkeypatch.setattr(main, "DB_PATH", tmp_path / "weather_cache.db")
    main.init_db()
    return TestClient(main.app)


def test_root_serves_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "location-input" in response.text
    assert "Get forecast" in response.text


def test_valid_forecast(client):
    response = client.get("/api/forecast", params={"location": "London"})
    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "London"
    assert isinstance(data["temperature"], (int, float))
    assert isinstance(data["condition"], str) and data["condition"]
    assert isinstance(data["humidity"], int)
    assert isinstance(data["wind"], (int, float))
    assert data["simulated"] is True
    assert "Simulated demo forecast" in data["disclaimer"]


def test_empty_location_returns_400(client):
    response = client.get("/api/forecast", params={"location": "   "})
    assert response.status_code == 400
    assert "error" in response.json()


def test_missing_location_returns_400(client):
    response = client.get("/api/forecast")
    assert response.status_code == 400
    assert "error" in response.json()


def test_too_long_location_returns_400(client):
    response = client.get("/api/forecast", params={"location": "x" * 101})
    assert response.status_code == 400
    assert "error" in response.json()


def test_deterministic_output(client):
    first = client.get("/api/forecast", params={"location": "Paris"}).json()
    second = client.get("/api/forecast", params={"location": "Paris"}).json()
    assert first["temperature"] == second["temperature"]
    assert first["condition"] == second["condition"]
    assert first["humidity"] == second["humidity"]
    assert first["wind"] == second["wind"]


def test_cache_reuse(client):
    first = client.get("/api/forecast", params={"location": "Tokyo"}).json()
    assert first["cached"] is False
    second = client.get("/api/forecast", params={"location": "Tokyo"}).json()
    assert second["cached"] is True
    assert second["temperature"] == first["temperature"]


def test_special_characters_are_safe(client):
    response = client.get("/api/forecast", params={"location": "S\u00e3o Paulo / \u5317\u4eac"})
    assert response.status_code == 200
    assert response.json()["location"] == "S\u00e3o Paulo / \u5317\u4eac"
