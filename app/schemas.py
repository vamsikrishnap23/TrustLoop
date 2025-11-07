from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# User schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    reputation: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Authentication schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Help Request schemas
class HelpRequestCreate(BaseModel):
    title: str
    description: str

class HelpRequestResponse(BaseModel):
    id: int
    title: str
    description: str
    created_by: int
    created_at: datetime
    creator: UserResponse
    
    class Config:
        from_attributes = True
