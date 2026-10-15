import hashlib
import os
from typing import Optional
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

# Global variable for the session serializer, initialized on startup
session_serializer: Optional[URLSafeTimedSerializer] = None

# --- Password Hashing Functions ---

def get_random_salt() -> bytes:
    """Generate a random salt for password hashing."""
    return os.urandom(16)

def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    """Hashes a password using PBKDF2 HMAC SHA256."""
    if salt is None:
        salt = get_random_salt()
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}:{dk.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    try:
        salt_hex, dk_hex = hashed_password.split(':')
        salt = bytes.fromhex(salt_hex)
        return hash_password(plain_password, salt) == hashed_password
    except ValueError:
        return False # Malformed hashed password

# --- Session Management Functions ---

def generate_secret_key() -> str:
    """Generates a random secret key for session serialization."""
    return os.urandom(32).hex()

def init_session_serializer(secret_key: str):
    """Initializes the global session serializer with a secret key."""
    global session_serializer
    session_serializer = URLSafeTimedSerializer(secret_key)

def create_session_token(user_id: int) -> str:
    """Creates a signed and timed session token for a user ID."""
    if session_serializer is None:
        raise RuntimeError("Session serializer not initialized. Call init_session_serializer first.")
    # Token expires in 1 day (86400 seconds)
    return session_serializer.dumps(user_id, salt='session-salt')

def decode_session_token(token: str) -> Optional[int]:
    """Decodes a session token and returns the user ID if valid and not expired."""
    if session_serializer is None:
        raise RuntimeError("Session serializer not initialized. Call init_session_serializer first.")
    try:
        # max_age in seconds (1 day)
        user_id = session_serializer.loads(token, salt='session-salt', max_age=86400)
        return int(user_id)
    except (BadTimeSignature, SignatureExpired, ValueError):
        return None
