# FastAPI Content Management System

A modern, scalable Content Management System built with FastAPI, SQLAlchemy, and PostgreSQL.

## Features

- 🚀 FastAPI for high-performance API
- 🔐 JWT-based authentication and authorization
- 📝 Content management with rich text support
- 🏷️ Category and tag organization
- 📁 Media file management
- 👥 User management with role-based access
- 🔍 Search and filtering capabilities
- 📊 Admin dashboard
- 🐳 Docker support
- 🧪 Comprehensive testing suite

## Quick Start

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your settings
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `uvicorn app.main:app --reload`

## Project Structure

The project follows a clean architecture pattern with separation of concerns:

- `app/api/` - API endpoints and routing
- `app/core/` - Core application logic and configuration
- `app/models/` - SQLAlchemy database models
- `app/schemas/` - Pydantic schemas for validation
- `app/services/` - Business logic layer
- `app/repositories/` - Data access layer
- `tests/` - Test suites

## Development

### Prerequisites

- Python 3.8+
- PostgreSQL
- Redis (optional, for caching)

### Setup

1. Create virtual environment: `python -m venv venv`
2. Activate virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements-dev.txt`
4. Run database migrations: `alembic upgrade head`
5. Start the development server: `uvicorn app.main:app --reload`

### Testing

Run tests with: `pytest`

### Docker

Build and run with Docker:

```bash
docker-compose up --build
```

## API Documentation

Once the application is running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT License
