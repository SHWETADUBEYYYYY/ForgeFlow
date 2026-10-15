"""Tiny calculator app: serves a single-page UI and a JSON compute endpoint."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="Calculator")
templates = Jinja2Templates(directory=str(FRONTEND_DIR))


class Calculation(BaseModel):
    a: float
    b: float
    op: str


def compute(a: float, b: float, op: str) -> float:
    """Apply a binary operator, raising ValueError for bad input."""
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    raise ValueError(f"Unknown operator: {op}")


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"title": "Calculator"}
    )


@app.post("/api/calculate")
def calculate(payload: Calculation):
    try:
        result = compute(payload.a, payload.b, payload.op)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    return {"result": result}
