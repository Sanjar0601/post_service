import enum
import secrets
import random
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    Boolean,
    Enum as SqlEnum,
    func
)
from db import Base
from datetime import datetime, timedelta



class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    password = Column(String(128), nullable=False)
    email = Column(String(254), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    verification_code = Column(String(64), nullable=True)
    verification_code_expires = Column(DateTime(timezone=True), nullable=True)
    is_verified = Column(Boolean, default=False)
    role = Column(SqlEnum(UserRole), default=UserRole.USER)

def generate_code():
    return str(random.randint(100000, 999999))

def get_code_expiry(minutes: int = 10) -> datetime:
    return datetime.utcnow() + timedelta(minutes=minutes)