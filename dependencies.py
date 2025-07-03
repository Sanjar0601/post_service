# dependencies.py
from config import settings
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from schemas import TokenData
from db import get_db
from models import User
from sqlalchemy.orm import Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return TokenData(**payload)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user_obj(
    token_data: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, token_data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def admin_required(current_user: User = Depends(get_current_user_obj)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
