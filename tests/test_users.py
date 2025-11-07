import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models import User

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

@pytest.fixture(scope="function")
def setup_database():
    """Create and clean up test database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_register_user_success(setup_database):
    """Test successful user registration."""
    response = client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["reputation"] == 0
    assert "id" in data
    assert "password" not in data  # Password should not be returned

def test_register_duplicate_username(setup_database):
    """Test registration with duplicate username fails."""
    # First registration
    client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "test1@example.com",
            "password": "testpassword123"
        }
    )
    
    # Second registration with same username
    response = client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "test2@example.com",
            "password": "testpassword456"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_register_duplicate_email(setup_database):
    """Test registration with duplicate email fails."""
    # First registration
    client.post(
        "/register",
        json={
            "username": "testuser1",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    # Second registration with same email
    response = client.post(
        "/register",
        json={
            "username": "testuser2",
            "email": "test@example.com",
            "password": "testpassword456"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_login_success(setup_database):
    """Test successful user login."""
    # Register user first
    client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    # Login
    response = client.post(
        "/login",
        json={
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "testuser"
    assert data["user"]["reputation"] == 0

def test_login_invalid_username(setup_database):
    """Test login with invalid username fails."""
    response = client.post(
        "/login",
        json={
            "username": "nonexistent",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_login_invalid_password(setup_database):
    """Test login with invalid password fails."""
    # Register user first
    client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    # Login with wrong password
    response = client.post(
        "/login",
        json={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_get_current_user(setup_database):
    """Test getting current user info with valid token."""
    # Register and login
    client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    login_response = client.post(
        "/login",
        json={
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Get current user
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["reputation"] == 0

def test_get_current_user_invalid_token(setup_database):
    """Test getting current user with invalid token fails."""
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
