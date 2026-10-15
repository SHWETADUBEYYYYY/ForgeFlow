"""Tiny FastAPI app that serves a static pencil showcase page.

Dependencies: fastapi, uvicorn, jinja2, httpx, pytest (no extra deps).
"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="Pencil Showcase")

# Serve static assets (CSS/JS/images) from the frontend directory.
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

templates = Jinja2Templates(directory=str(FRONTEND_DIR))

# Simple demo data describing the pencil shown on the page.
PENCIL = {
    "name": "Classic No. 2 Pencil",
    "type": "Graphite writing pencil",
    "hardness": "HB (No. 2)",
    "length": "19 cm (7.5 in)",
    "material": "Cedar wood, graphite core, rubber eraser",
    "description": (
        "A dependable everyday pencil with a hexagonal cedar barrel, "
        "a smooth graphite core, and a soft rubber eraser. "
        "Ideal for writing, sketching, and standardized tests."
    ),
}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the pencil showcase page."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"pencil": PENCIL},
    )
