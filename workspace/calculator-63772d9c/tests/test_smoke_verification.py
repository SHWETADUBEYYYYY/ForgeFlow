"""Independent smoke verification of the running app surface.

These checks go beyond the unit tests: they exercise the served HTML page and
the JSON endpoint end to end through the ASGI app, asserting the exact
contracts the README documents.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_index_serves_calculator_page():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    html = r.text
    assert 'id="display"' in html
    for digit in "0123456789":
        assert f'data-digit="{digit}"' in html
    for op in ["+", "-", "*", "/"]:
        assert f'data-op="{op}"' in html
    assert 'data-action="equals"' in html
    assert 'data-action="clear"' in html


def test_all_operators_end_to_end():
    cases = [
        ({"a": 2, "b": 3, "op": "+"}, 5),
        ({"a": 9, "b": 4, "op": "-"}, 5),
        ({"a": 6, "b": 7, "op": "*"}, 42),
        ({"a": 8, "b": 2, "op": "/"}, 4),
    ]
    for payload, expected in cases:
        r = client.post("/api/calculate", json=payload)
        assert r.status_code == 200, payload
        assert r.json() == {"result": expected}, payload


def test_divide_by_zero_contract():
    r = client.post("/api/calculate", json={"a": 5, "b": 0, "op": "/"})
    assert r.status_code == 400
    body = r.json()
    assert "error" in body
    assert "result" not in body


def test_unknown_operator_contract():
    r = client.post("/api/calculate", json={"a": 1, "b": 2, "op": "%"})
    assert r.status_code == 400
    assert "error" in r.json()


def test_malformed_payload_contract():
    r = client.post("/api/calculate", json={"a": "nope", "b": 2, "op": "+"})
    assert r.status_code == 422


@pytest.mark.parametrize(
    "a,b,op,expected",
    [(-2.5, 1.25, "+", -1.25), (1.25, 2.5, "-", -1.25),
     (-1.5, -2, "*", 3), (-7.5, 2.5, "/", -3)],
)
def test_decimal_and_negative_operands(a, b, op, expected):
    response = client.post("/api/calculate", json={"a": a, "b": b, "op": op})
    assert response.status_code == 200
    assert response.json() == {"result": expected}


@pytest.mark.parametrize("payload", [
    {},
    {"a": 1, "op": "+"},
    {"a": None, "b": 2, "op": "+"},
    {"a": 1, "b": "invalid", "op": "+"},
    {"a": [], "b": 2, "op": "+"},
])
def test_invalid_payloads(payload):
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()
