# TrustLoop

A community-driven help exchange platform where users can post requests for help, offer help to others, and build reputation through positive interactions.

## Features (Review 1 Prototype)

- ✅ User registration with reputation system
- ✅ User login with basic authentication  
- ✅ Create and view help requests
- ✅ Reputation tracking (starts at 0 for new users)

## Setup

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate virtual environment:
```bash
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

5. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

- `POST /register` - Register a new user
- `POST /login` - Login user
- `POST /requests` - Create a help request
- `GET /requests` - Get all help requests

## Testing

Run tests with:
```bash
pytest
```
