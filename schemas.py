from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Base schema for user, shared by multiple other schemas
class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    email: EmailStr


# Schema used when creating a new user (e.g., during registration)
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


# schemas.py
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None  


# Schema used for user login
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Schema for returning user data (e.g., in responses)
# schemas.py
class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_verified: bool
    role: str

    class Config:
        orm_mode = True


# Schema used when updating user info (all fields optional)
class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr]
    password: Optional[str] = Field(None, min_length=6, max_length=128)


# Schema returned when a user logs in (JWT or access token)
class Token(BaseModel):
    access_token: str
    token_type: str  # usually "bearer"


# Schema representing the data decoded from the token payload
class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    email_verified: Optional[bool] = False


class VerificationRequest(BaseModel):
    email: EmailStr
    code: str