from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend import crud, models
from backend.auth import decode_session_token

def get_db() -> Generator:
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[models.User]:
    """Dependency to get the current authenticated user from session cookie."""
    session_token = request.cookies.get("session_token")
    if not session_token:
        return None

    user_id = decode_session_token(session_token)
    if user_id is None:
        return None

    user = crud.get_user_by_id(db, user_id=user_id)
    if user is None:
        return None
    return user

def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Dependency to get the current authenticated user, raising 401 if not found."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user
