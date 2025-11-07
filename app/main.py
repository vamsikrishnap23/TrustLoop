from fastapi import FastAPI, HTTPException, Depends, status, Path
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Optional


from .database import get_db, engine
from .models import Base, User, HelpRequest
from .schemas import (
    UserCreate, UserResponse, LoginRequest, LoginResponse,
    HelpRequestCreate, HelpRequestResponse
)
from .auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from sqlalchemy.exc import IntegrityError


# FastAPI app
app = FastAPI(
    title="TrustLoop API",
    description="Community-driven help exchange platform",
    version="1.0.0"
)

# Create database tables
Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    """Root endpoint - API health check."""
    return {"message": "Welcome to TrustLoop API", "status": "healthy"}

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    db_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
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

@app.post("/login", response_model=LoginResponse)
def login_user(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login user and return JWT token."""
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@app.post("/requests", response_model=HelpRequestResponse, status_code=status.HTTP_201_CREATED)
def create_help_request(
    request: HelpRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new help request (requires authentication)."""
    db_request = HelpRequest(
        title=request.title,
        description=request.description,
        created_by=current_user.id
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    return db_request

@app.get("/requests", response_model=List[HelpRequestResponse])
def get_help_requests(db: Session = Depends(get_db)):
    """Get all help requests with user information."""
    requests = db.query(HelpRequest).all()
    return requests

@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information (requires authentication)."""
    return current_user






# --- User Management Endpoints ---
@app.get("/users", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    """Get all registered users."""
    users = db.query(User).all()
    return users

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    """Get a user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    """Delete a user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int = Path(..., gt=0),
    username: Optional[str] = None,
    email: Optional[str] = None,
    reputation: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Update a user's username, email, or reputation."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if username:
        user.username = username
    if email:
        user.email = email
    if reputation is not None:
        user.reputation = reputation
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or email already exists.")
    return user






if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)