"""API tests for the calculator backend."""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_index_renders_calculator_page():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "Calculator" in html
    for digit in "0123456789":
        assert f'data-digit="{digit}"' in html
    for op in ["+", "-", "*", "/"]:
        assert f'data-op="{op}"' in html
    assert 'data-action="equals"' in html
    assert 'data-action="clear"' in html


def test_addition():
    r = client.post("/api/calculate", json={"a": 2, "b": 3, "op": "+"})
    assert r.status_code == 200
    assert r.json()["result"] == 5


def test_subtraction():
    r = client.post("/api/calculate", json={"a": 9, "b": 4, "op": "-"})
    assert r.status_code == 200
    assert r.json()["result"] == 5


def test_multiplication():
    r = client.post("/api/calculate", json={"a": 6, "b": 7, "op": "*"})
    assert r.status_code == 200
    assert r.json()["result"] == 42


def test_division():
    r = client.post("/api/calculate", json={"a": 8, "b": 2, "op": "/"})
    assert r.status_code == 200
    assert r.json()["result"] == 4


def test_division_by_zero_returns_error():
    r = client.post("/api/calculate", json={"a": 5, "b": 0, "op": "/"})
    assert r.status_code == 400
    body = r.json()
    assert "error" in body
    assert "divide by zero" in body["error"].lower()
    assert "result" not in body


def test_unknown_operator_returns_error():
    r = client.post("/api/calculate", json={"a": 1, "b": 2, "op": "%"})
    assert r.status_code == 400
    assert "error" in r.json()


def test_malformed_payload_returns_422():
    r = client.post("/api/calculate", json={"a": "not-a-number", "b": 2, "op": "+"})
    assert r.status_code == 422
