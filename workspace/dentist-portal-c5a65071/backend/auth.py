"""Password hashing and session helpers for the Anna Dental Clinic portal."""

import hashlib
import hmac
import os
import secrets

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .models import SessionLocal, User

# Session secret: prefer an environment variable, otherwise generate a random
# per-process secret so nothing sensitive is ever hard-coded in source.
SESSION_SECRET = os.environ.get("SESSION_SECRET") or secrets.token_hex(32)
SESSION_COOKIE = "adc_session"
SESSION_MAX_AGE = 60 * 60 * 8  # 8 hours

_serializer = URLSafeTimedSerializer(SESSION_SECRET, salt="adc-session")

PBKDF2_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    """Return a salted pbkdf2_hmac hash string for the given password."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Check a plaintext password against a stored pbkdf2 hash."""
    try:
        algorithm, iterations, salt, digest_hex = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        expected = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)
        )
        return hmac.compare_digest(expected.hex(), digest_hex)
    except (ValueError, AttributeError):
        return False


def create_session_token(user_id: int) -> str:
    """Sign a session token containing the user id."""
    return _serializer.dumps({"user_id": user_id})


def read_session_token(token: str):
    """Return the user id from a valid token, or None if invalid/expired."""
    try:
        data = _serializer.loads(token, max_age=SESSION_MAX_AGE)
        return data.get("user_id")
    except (BadSignature, SignatureExpired):
        return None


def get_user_by_username(username: str):
    db = SessionLocal()
    try:
        return db.query(User).filter(User.username == username).first()
    finally:
        db.close()


def get_user_by_id(user_id: int):
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


def seed_demo_user():
    """Create a demo staff user on first run if none exists.

    Credentials come from environment variables when provided; otherwise a
    documented default (staff / dental123) is used for local demos only.
    """
    username = os.environ.get("STAFF_USERNAME", "staff")
    password = os.environ.get("STAFF_PASSWORD", "dental123")
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing is None:
            db.add(User(username=username, password_hash=hash_password(password)))
            db.commit()
    finally:
        db.close()
