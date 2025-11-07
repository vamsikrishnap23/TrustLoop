from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
import bcrypt
from datetime import datetime
import os

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./trustloop.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    reputation = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to help requests
    help_requests = relationship("HelpRequest", back_populates="creator")

class HelpRequest(Base):
    __tablename__ = "help_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to user
    creator = relationship("User", back_populates="help_requests")

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models for API
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    reputation: int
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

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

# FastAPI app
app = FastAPI(title="TrustLoop", description="Community-driven help exchange platform")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# API Endpoints
@app.get("/")
def read_root():
    return {"message": "Welcome to TrustLoop API"}

@app.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Create new user
    hashed_password = hash_password(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        reputation=0
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/login")
def login_user(login_data: LoginRequest, db: Session = Depends(get_db)):
    # Find user
    db_user = db.query(User).filter(User.username == login_data.username).first()
    if not db_user or not verify_password(login_data.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return {"message": "Login successful", "user_id": db_user.id, "reputation": db_user.reputation}

@app.post("/requests", response_model=HelpRequestResponse)
def create_help_request(request: HelpRequestCreate, user_id: int, db: Session = Depends(get_db)):
    # Verify user exists
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create help request
    db_request = HelpRequest(
        title=request.title,
        description=request.description,
        created_by=user_id
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    return db_request

@app.get("/requests", response_model=list[HelpRequestResponse])
def get_help_requests(db: Session = Depends(get_db)):
    requests = db.query(HelpRequest).all()
    return requests

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
