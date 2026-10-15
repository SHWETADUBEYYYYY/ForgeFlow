from pathlib import Path
import math

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(title="BMI Calculator")
FRONTEND = Path(__file__).resolve().parent.parent / "frontend" / "index.html"


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exception):
    # Invalid input may contain NaN or Infinity; do not echo it into JSON.
    details = [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in exception.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": details})


class Measurements(BaseModel):
    height_cm: float = Field(gt=0, allow_inf_nan=False)
    weight_kg: float = Field(gt=0, allow_inf_nan=False)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(FRONTEND)


@app.post("/api/bmi")
def calculate_bmi(measurements: Measurements):
    height_m = measurements.height_cm / 100
    try:
        bmi = measurements.weight_kg / height_m / height_m
    except (ZeroDivisionError, OverflowError):
        bmi = math.inf
    if not math.isfinite(bmi) or bmi <= 0:
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["body"], "msg": "Measurements are outside the calculable range.", "type": "value_error"}],
        )
    # Classify before rounding so display precision never changes the category.
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal weight"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obesity"
    return {"bmi": round(bmi, 1), "category": category}
