from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend import crud, schemas, auth
from backend.database import get_db
from backend.dependencies import get_current_user

router = APIRouter(tags=["auth"])

@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@router.post("/token")
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    session_token = auth.create_session_token(user.id)
    response.set_cookie(key="session_token", value=session_token, httponly=True, samesite="Lax", secure=False, max_age=86400) # 1 day expiration
    return {"message": "Login successful"}

@router.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    # get_current_user now returns models.User, which Pydantic will convert to schemas.User
    return current_user

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="session_token")
    return {"message": "Successfully logged out"}
