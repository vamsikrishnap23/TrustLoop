# TrustLoop Project Structure

```
TrustLoop/
├── venv/                          # Virtual environment (already exists)
├── app/                           # Main application package
│   ├── __init__.py               # Package initialization
│   ├── main.py                   # FastAPI app entry point
│   ├── models.py                 # SQLAlchemy database models
│   ├── schemas.py                # Pydantic models for API
│   ├── database.py               # Database configuration
│   └── auth.py                   # Authentication utilities
├── tests/                        # Test package
│   ├── __init__.py               # Test package initialization
│   ├── test_users.py             # User registration/login tests
│   └── test_requests.py          # Help requests tests
├── requirements.txt              # Python dependencies (already exists)
├── README.md                     # Project documentation
└── .gitignore                    # Git ignore file
```

## Key Components:

### 1. **app/main.py** - FastAPI application with endpoints:

- `POST /register` - User registration
- `POST /login` - User login (returns JWT token)
- `POST /requests` - Create help request (requires JWT auth)
- `GET /requests` - Get all help requests

### 2. **app/models.py** - Database models:

- `User` model (id, username, email, password_hash, reputation)
- `HelpRequest` model (id, title, description, created_by, created_at)

### 3. **app/schemas.py** - Pydantic models for API validation:

- `UserCreate`, `UserResponse`
- `LoginRequest`, `LoginResponse` (with JWT token)
- `HelpRequestCreate`, `HelpRequestResponse`

### 4. **tests/** - Unit tests:

- Test user registration (200 OK)
- Test posting help requests
- Test fetching requests returns list

### 5. **Database**: SQLite (trustloop.db) for simplicity

This structure follows FastAPI best practices and keeps the code organized and testable.
