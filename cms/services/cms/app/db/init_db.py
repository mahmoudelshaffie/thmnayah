"""
Database initialization utilities.

This module provides functions for:
- Creating database tables
- Initial data seeding
- Database health checks
- Development utilities
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import text

from db.base import Base
from db.session import engine, SessionLocal
from core.config import settings
from repositories.category import CategoryRepository
from api.v1.models.categories import CategoryCreate

logger = logging.getLogger(__name__)

category_repo = CategoryRepository()
def create_tables():
    """
    Create all database tables.
    
    This creates tables based on SQLAlchemy models.
    In production, use Alembic migrations instead.
    """
    try:
        Base._metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def drop_tables():
    """
    Drop all database tables.
    
    WARNING: This will delete all data!
    Use only in development/testing.
    """
    try:
        Base._metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


def init_db(db: Session) -> None:
    """
    Initialize database with initial data.
    
    Args:
        db: Database session
    """
    try:
        # Create PostgreSQL extensions if needed
        if settings.DATABASE_URL.startswith('postgresql'):
            create_extensions(db)
        
        # Add initial data here
        create_initial_categories(db)
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        db.rollback()
        raise
    else:
        db.commit()


def create_extensions(db: Session) -> None:
    """
    Create required PostgreSQL extensions.
    
    Args:
        db: Database session
    """
    extensions = [
        'uuid-ossp',     # For UUID generation
        'pg_trgm',       # For similarity search
        'btree_gin',     # For GIN indexes on btree types
        'unaccent',      # For accent-insensitive search
    ]
    
    for ext in extensions:
        try:
            db.execute(text(f'CREATE EXTENSION IF NOT EXISTS "{ext}"'))
            logger.debug(f"Created extension: {ext}")
        except Exception as e:
            logger.warning(f"Failed to create extension {ext}: {e}")


def create_initial_categories(db: Session) -> None:
    """
    Create initial category structure.
    
    Args:
        db: Database session
    """
    from models.category import Category
    from api.v1.models.categories import CategoryType, CategoryVisibility
    
    # Check if categories already exist
    if db.query(Category).first():
        logger.info("Categories already exist, skipping initial creation")
        return
    
    # Create root categories
    initial_categories = [
        {
            "name": {
                "en": "Sciences",
                "ar": "'D9DHE",
                "fr": "Sciences"
            },
            "description": {
                "en": "Scientific content and educational materials",
                "ar": "'DE-*HI 'D9DEJ H'DEH'/ 'D*9DJEJ)",
                "fr": "Contenu scientifique et materiel podagogique"
            },
            "category_type": CategoryType.TOPIC,
            "visibility": CategoryVisibility.PUBLIC,
            "is_active": True,
            "sort_order": 1
        },
        {
            "name": {
                "en": "Technology",
                "ar": "'D*CFHDH,J'",
                "fr": "Technologie"
            },
            "description": {
                "en": "Technology and programming content",
                "ar": "E-*HI 'D*CFHDH,J' H'D(1E,)", 
                "fr": "Contenu technologie et programmation"
            },
            "category_type": CategoryType.TOPIC,
            "visibility": CategoryVisibility.PUBLIC,
            "is_active": True,
            "sort_order": 2
        },
        {
            "name": {
                "en": "Video",
                "ar": "AJ/JH",
                "fr": "Vid�o"
            },
            "description": {
                "en": "Video content format",
                "ar": "*F3JB 'DE-*HI 'DE1&J",
                "fr": "Format de contenu vid�o"
            },
            "category_type": CategoryType.FORMAT,
            "visibility": CategoryVisibility.PUBLIC,
            "is_active": True,
            "sort_order": 1
        }
    ]


    for cat_data in initial_categories:
        category = CategoryCreate(**cat_data)
        category_repo.create_category(db=db, category_data=category)

        
    logger.info(f"Created {len(initial_categories)} initial categories")


def check_database_health() -> dict:
    """
    Perform database health check.
    
    Returns:
        dict: Health check results
    """
    health = {
        "status": "healthy",
        "checks": {},
        "info": {}
    }
    
    try:
        with SessionLocal() as db:
            # Test basic connection
            db.execute(text("SELECT 1"))
            health["checks"]["connection"] = "ok"
            
            # Check if tables exist
            from models.category import Category
            category_count = db.query(Category).count()
            health["checks"]["tables"] = "ok"
            health["info"]["category_count"] = category_count
            
            # Check database version
            if settings.DATABASE_URL.startswith('postgresql'):
                result = db.execute(text("SELECT version()")).fetchone()
                health["info"]["database_version"] = result[0] if result else "unknown"
            
    except Exception as e:
        health["status"] = "unhealthy"
        health["error"] = str(e)
        logger.error(f"Database health check failed: {e}")
    
    return health


# Development utilities
def reset_database():
    """
    Reset database for development.
    
    WARNING: This drops all tables and recreates them!
    """
    logger.warning("Resetting database - all data will be lost!")
    drop_tables()
    create_tables()
    
    with SessionLocal() as db:
        init_db(db)
    
    logger.info("Database reset complete")


if __name__ == "__main__":
    # Allow running this script directly for development
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create":
            create_tables()
        elif command == "drop":
            drop_tables()
        elif command == "reset":
            reset_database()
        elif command == "health":
            health = check_database_health()
            print(health)
        else:
            print("Usage: python init_db.py [create|drop|reset|health]")
    else:
        print("Usage: python init_db.py [create|drop|reset|health]")