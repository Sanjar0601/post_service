from fastapi import FastAPI
from db import *
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models import UserRole, get_code_expiry, generate_code
from schemas import UserCreate, Token, VerificationRequest
from auth import verify_password, create_access_token, decode_access_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.future import select
from datetime import datetime
from typing import List
from models import User
from schemas import UserRead, UserUpdate
from auth import hash_password
from dependencies import admin_required, get_current_user_obj

app = FastAPI()

Base.metadata.create_all(bind=engine)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Register user
@app.post("/register",
          response_model=UserRead,
          summary="Register a new user",
          description='''Create a new user account with email, username, and password. 
          A verification code will be printed to the console.User is not verified by default.'''
)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.execute(select(User).where(User.email == user.email)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    code = generate_code()
    expires = get_code_expiry()

    new_user = User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        role=UserRole.USER,
        is_verified=False,
        verification_code=code,
        verification_code_expires=expires
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    print(f"[VERIFY] Code for {new_user.email}: {code} (expires at {expires})")
    return new_user




@app.post("/login",
          response_model=Token,
          summary="User login",
          description="Authenticate a user using email and password. Returns a JWT access token if credentials are valid."
)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.execute(select(User).where(User.email == form_data.username)).scalar_one_or_none()
    if not db_user or not verify_password(form_data.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"user_id": db_user.id, "email": db_user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.get(
    "/me",
    response_model=UserRead,
    summary="Get current authenticated user",
    description="Returns the details of the currently authenticated user. Requires a valid JWT access token."
)
def read_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    token_data = decode_access_token(token)
    if not token_data or not token_data.user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    db_user = db.get(User, token_data.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post(
    "/auth/verify",
    summary="Verify user with code",
    description="Submit the verification code (printed in console) to verify a newly registered account. Code must be valid and not expired."
)
def verify_user(request: VerificationRequest,db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == request.email)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        raise HTTPException(status_code=400, detail="User already verified")
    if user.verification_code != request.code:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    if not user.verification_code_expires or user.verification_code_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification code expired")

    user.is_verified = True
    user.verification_code = None
    user.verification_code_expires = None
    db.commit()

    return {"message": "Verification successful!"}


@app.get(
    "/",
    response_model=List[UserRead],
    summary="List all users (admin only)",
    description="Returns a list of all users in the system. Access restricted to admin users only."
)
def get_users(db: Session = Depends(get_db), _: User = Depends(admin_required)):
    return db.query(User).all()

@app.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get user by ID (admin only)",
    description="Retrieve a specific user's details by their ID. Only admins are authorized to access this endpoint."
)

def get_user_by_id(user_id: int, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Update user info",
    description="Update the authenticated user's own information (username, email, password), or allow admins to update any user."
)
def update_user(
    user_id: int,
    updates: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_obj)
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.id != user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to update this user")

    if updates.username:
        user.username = updates.username
    if updates.email:
        user.email = updates.email
    if updates.password:
        user.password = hash_password(updates.password)

    db.commit()
    db.refresh(user)
    return user

@app.delete(
    "/{user_id}",
    summary="Delete user (admin only)",
    description="Delete a user account by ID. Only accessible by admin users."
)
def delete_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully."}
