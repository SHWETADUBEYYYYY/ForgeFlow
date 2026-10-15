"""API tests for the Anna Dental Clinic portal."""

import os
import tempfile

import pytest

# Use a temporary SQLite database so tests never touch the demo database.
_tmp_dir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp_dir, 'test.db')}"
os.environ["SESSION_SECRET"] = "test-secret"
os.environ["STAFF_USERNAME"] = "staff"
os.environ["STAFF_PASSWORD"] = "dental123"

from fastapi.testclient import TestClient  # noqa: E402

from backend.auth import hash_password, verify_password  # noqa: E402
from backend.main import app  # noqa: E402
from backend.models import AppointmentRequest, SessionLocal, User, init_db  # noqa: E402


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_appointments():
    db = SessionLocal()
    try:
        db.query(AppointmentRequest).delete()
        db.commit()
    finally:
        db.close()
    yield


def test_landing_page_shows_clinic_info(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert "Anna Dental Clinic" in body
    assert "Our Services" in body
    assert "Request an Appointment" in body
    assert "+1 (555) 010-2030" in body


def test_static_assets_are_served(client):
    css = client.get("/static/style.css")
    js = client.get("/static/app.js")
    assert css.status_code == 200
    assert js.status_code == 200
    assert "--brand" in css.text


def test_valid_appointment_is_stored(client):
    response = client.post(
        "/appointments",
        data={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "555-1234",
            "preferred_date": "2024-06-01",
            "preferred_time": "10:00",
            "message": "Routine cleaning",
        },
    )
    assert response.status_code == 200
    assert "appointment request has been received" in response.text

    db = SessionLocal()
    try:
        stored = db.query(AppointmentRequest).filter_by(email="jane@example.com").all()
        assert len(stored) == 1
        assert stored[0].name == "Jane Doe"
        assert stored[0].status == "new"
    finally:
        db.close()


def test_invalid_appointment_shows_errors_and_stores_nothing(client):
    response = client.post(
        "/appointments",
        data={
            "name": "",
            "email": "not-an-email",
            "phone": "",
            "preferred_date": "",
            "preferred_time": "",
            "message": "",
        },
    )
    assert response.status_code == 400
    assert "Please enter your name." in response.text
    assert "Please enter a valid email address." in response.text

    db = SessionLocal()
    try:
        assert db.query(AppointmentRequest).count() == 0
    finally:
        db.close()


def test_admin_requires_login(client):
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_login_with_wrong_credentials_fails(client):
    response = client.post(
        "/login", data={"username": "staff", "password": "wrong"}
    )
    assert response.status_code == 401
    assert "Invalid username or password." in response.text
    assert "adc_session" not in response.cookies


def test_login_and_admin_flow(client):
    login = client.post(
        "/login",
        data={"username": "staff", "password": "dental123"},
        follow_redirects=False,
    )
    assert login.status_code == 303
    assert login.headers["location"] == "/admin"
    assert "adc_session" in login.cookies

    client.post(
        "/appointments",
        data={
            "name": "Sam Smith",
            "email": "sam@example.com",
            "phone": "555-9999",
            "preferred_date": "2024-07-15",
            "preferred_time": "14:30",
            "message": "Check-up",
        },
    )

    dashboard = client.get("/admin")
    assert dashboard.status_code == 200
    assert "Sam Smith" in dashboard.text
    assert "sam@example.com" in dashboard.text

    db = SessionLocal()
    try:
        appointment = db.query(AppointmentRequest).filter_by(email="sam@example.com").one()
        appointment_id = appointment.id
    finally:
        db.close()

    update = client.post(
        f"/admin/appointments/{appointment_id}/status",
        data={"status": "contacted"},
        follow_redirects=False,
    )
    assert update.status_code == 303

    refreshed = client.get("/admin")
    assert "badge-contacted" in refreshed.text

    logout = client.get("/logout", follow_redirects=False)
    assert logout.status_code == 303
    assert logout.headers["location"] == "/login"

    after_logout = client.get("/admin", follow_redirects=False)
    assert after_logout.status_code == 303
    assert after_logout.headers["location"] == "/login"


def test_password_hashing_roundtrip():
    stored = hash_password("s3cret")
    assert stored.startswith("pbkdf2_sha256$")
    assert "s3cret" not in stored
    assert verify_password("s3cret", stored)
    assert not verify_password("wrong", stored)


def test_seeded_user_password_is_hashed(client):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(username="staff").first()
        assert user is not None
        assert user.password_hash != "dental123"
        assert user.password_hash.startswith("pbkdf2_sha256$")
    finally:
        db.close()
