from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI(title="Air Studio — Unofficial Concept")
FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/", response_class=FileResponse)
def homepage():
    return FileResponse(FRONTEND / "index.html")
