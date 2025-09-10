"""
Database session management for SQLAlchemy with PostgreSQL.

This module handles:
- SQLAlchemy engine creation with connection pooling
- Session factory configuration
- Database dependency injection for FastAPI
- Connection management and cleanup
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from core.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with PostgreSQL optimizations
engine = create_engine(
    settings.DATABASE_URL,
    # Connection pool settings for production
    pool_size=10,          # Number of connections to maintain in pool
    max_overflow=20,       # Maximum additional connections beyond pool_size  
    pool_timeout=30,       # Timeout for getting connection from pool
    pool_recycle=3600,     # Recycle connections after 1 hour
    pool_pre_ping=True,    # Validate connections before use
    # Performance settings
    echo=settings.DEBUG if hasattr(settings, 'DEBUG') else False,  # Log SQL queries in debug mode
    future=True,           # Use SQLAlchemy 2.0 style
    # PostgreSQL specific optimizations
    connect_args={
        "options": "-c timezone=utc",  # Set timezone to UTC
        "application_name": settings.PROJECT_NAME,  # Identify connections in PostgreSQL logs
        # Connection timeouts
        "connect_timeout": 10,
        # "server_settings": {
        #     "jit": "off",  # Disable JIT for faster connection times
        # }
    } if settings.DATABASE_URL.startswith('postgresql') else {}
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(
    autocommit=False,      # Manual transaction control
    autoflush=False,       # Manual flush control for better performance
    bind=engine,
    expire_on_commit=False  # Keep objects accessible after commit
)


def get_db() -> Generator[Session, None, None]:
    """
    Database dependency for FastAPI.
    
    Creates a database session and ensures it's properly closed.
    Use this as a dependency in your FastAPI endpoints.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        @app.get("/users/")
        def read_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_db_session() -> Session:
    """
    Create a database session for manual use.
    
    Note: Remember to close the session manually when using this function.
    Prefer using get_db() as a FastAPI dependency when possible.
    
    Returns:
        Session: SQLAlchemy database session
    """
    return SessionLocal()


# Connection health check
def check_db_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        logger.info("Checking database connection...")
        with engine.connect() as conn:

            conn.execute(text("SELECT table_name FROM information_schema.tables"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


# Database connection info
def get_db_info() -> dict:
    """
    Get database connection information.
    
    Returns:
        dict: Database connection details
    """
    return {
        "url": settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL,
        "pool_size": engine.pool.size(),
        "pool_checked_in": engine.pool.checkedin(),
        "pool_checked_out": engine.pool.checkedout(),
        "pool_overflow": engine.pool.overflow(),
    }