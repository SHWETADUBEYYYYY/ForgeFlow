# Calculator

A single-page calculator served by FastAPI. The vanilla-JavaScript interface
calculates locally; a separate JSON API exposes the same four operations.

## Run

The ASGI entry point is `backend.main:app`; `GET /` serves the calculator.
Runtime dependencies are FastAPI, Pydantic, and Jinja2. Tests also use pytest
and httpx.

Use the hosting platform's ASGI launch mechanism with that entry point.
This verification session exposes no preview-launch tool or launch configuration,
so no platform launch command or successful preview can be confirmed. A standalone
launch requires an ASGI server, which is outside this session's supported tools;
no additional server dependency is introduced here.

## Usage

Click digits and `.` to enter a number, choose `+`, `-`, `*`, or `/`, enter the
second number, then click `=`. `Clear` resets the display and pending calculation.
Division by zero displays `Cannot divide by zero`; entering a number starts again.

## API

`POST /api/calculate` accepts JSON:

```json
{"a": 2, "b": 3, "op": "+"}
```

Returns `{"result": 5}`. Division by zero and unknown operators return HTTP 400
with `{"error": "..."}`. Missing or invalid operands return HTTP 422 with
validation details. Numeric operands include negative and decimal values.

## Verification

From the project root:

```bash
python -m pytest -q tests/test_calculator.py
python -m pytest -q tests/test_smoke_verification.py
```

Recorded independent runs passed: **8 tests** and **14 tests**, respectively.
Each run reported one Starlette/httpx deprecation warning. Coverage includes
served HTML, four arithmetic operations, negative and decimal operands, and
HTTP 400/422 error contracts.

TestClient checks do not execute JavaScript. No browser-interaction tool is
available in this session, so these browser checks remain **unverified**:

- `2 + 3 = 5`, `9 - 4 = 5`, `6 * 7 = 42`, and `8 / 2 = 4`.
- Decimal entry and duplicate decimal-point prevention.
- Clear resetting both the display and a pending operation.
- Chained operations and replacing a pending operator.
- Visible division-by-zero errors followed by successful new input.

Preview launch is also unverified because no preview launcher is exposed.
