"""Smoke tests for the pencil showcase page."""
from fastapi.testclient import TestClient

from backend.main import PENCIL, app

client = TestClient(app)


def test_index_returns_200() -> None:
    response = client.get("/")
    assert response.status_code == 200


def test_index_shows_pencil_name_and_info() -> None:
    response = client.get("/")
    body = response.text
    assert PENCIL["name"] in body
    for key in ("type", "hardness", "length", "material", "description"):
        assert PENCIL[key] in body


def test_index_contains_pencil_illustration() -> None:
    response = client.get("/")
    body = response.text
    for cls in ("eraser", "ferrule", "body", "tip", "lead"):
        assert f'class="{cls}"' in body
