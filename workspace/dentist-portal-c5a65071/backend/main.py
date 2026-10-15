"""FastAPI application for the Anna Dental Clinic portal."""

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .auth import (
    SESSION_COOKIE,
    create_session_token,
    get_user_by_id,
    get_user_by_username,
    read_session_token,
    seed_demo_user,
    verify_password,
)
from .models import AppointmentRequest, get_session, init_db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed the demo staff user on startup."""
    init_db()
    seed_demo_user()
    yield


app = FastAPI(title="Anna Dental Clinic Portal", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")
templates = Jinja2Templates(directory=FRONTEND_DIR)


def current_user(request: Request):
    """Return the logged-in staff user, or None."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    user_id = read_session_token(token)
    if not user_id:
        return None
    return get_user_by_id(user_id)


@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"clinic_name": "Anna Dental Clinic"},
    )


@app.post("/appointments", response_class=HTMLResponse)
def create_appointment(
    request: Request,
    name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    preferred_date: str = Form(""),
    preferred_time: str = Form(""),
    message: str = Form(""),
    db: Session = Depends(get_session),
):
    errors = {}
    if not name.strip():
        errors["name"] = "Please enter your name."
    if "@" not in email or "." not in email.split("@")[-1]:
        errors["email"] = "Please enter a valid email address."
    if not phone.strip():
        errors["phone"] = "Please enter a phone number."
    if not preferred_date.strip():
        errors["preferred_date"] = "Please choose a preferred date."

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "clinic_name": "Anna Dental Clinic",
                "errors": errors,
                "form": {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "preferred_date": preferred_date,
                    "preferred_time": preferred_time,
                    "message": message,
                },
            },
            status_code=400,
        )

    db.add(
        AppointmentRequest(
            name=name.strip(),
            email=email.strip(),
            phone=phone.strip(),
            preferred_date=preferred_date.strip(),
            preferred_time=preferred_time.strip(),
            message=message.strip(),
        )
    )
    db.commit()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "clinic_name": "Anna Dental Clinic",
            "success": "Thank you! Your appointment request has been received.",
        },
    )


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    if current_user(request):
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse(
        request=request, name="login.html", context={"clinic_name": "Anna Dental Clinic"}
    )


@app.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
):
    user = get_user_by_username(username.strip())
    if user is None or not verify_password(password, user.password_hash):
        # A failed login must not leave any prior session active, so clear the
        # cookie on the error response as well.
        response = templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"clinic_name": "Anna Dental Clinic", "error": "Invalid username or password."},
            status_code=401,
        )
        response.delete_cookie(SESSION_COOKIE)
        return response

    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(user.id),
        httponly=True,
        samesite="lax",
    )
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_session)):
    user = current_user(request)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    appointments = (
        db.query(AppointmentRequest).order_by(AppointmentRequest.created_at.desc()).all()
    )
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "clinic_name": "Anna Dental Clinic",
            "username": user.username,
            "appointments": [a.as_dict() for a in appointments],
        },
    )


@app.post("/admin/appointments/{appointment_id}/status")
def update_status(
    request: Request,
    appointment_id: int,
    status: str = Form(""),
    db: Session = Depends(get_session),
):
    if current_user(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    allowed = {"new", "contacted", "closed"}
    appointment = db.query(AppointmentRequest).filter(AppointmentRequest.id == appointment_id).first()
    if appointment is not None and status in allowed:
        appointment.status = status
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)
