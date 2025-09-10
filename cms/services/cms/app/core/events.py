"""
Application lifecycle event handlers.

Handles FastAPI startup and shutdown events for:
- Database initialization
- Connection pool management
- Health check setup
- Cleanup operations
"""

import logging
from typing import Callable

from db.session import engine, check_db_connection
from db.init_db import init_db, SessionLocal

logger = logging.getLogger(__name__)


def create_start_app_handler() -> Callable:
    """
    Create application startup handler.
    
    Returns:
        Callable: Startup event handler function
    """
    def startup_handler() -> None:
        """Handle application startup."""
        logger.info("Starting CMS application...")
        
        try:
            # Check database connection
            if not check_db_connection():
                logger.error("Database connection failed on startup")
                raise RuntimeError("Database connection failed")
            
            logger.info("Database connection established")
            
            # Initialize database with extensions and initial data
            with SessionLocal() as db:
                init_db(db)
            
            logger.info("CMS application startup complete")
            
        except Exception as e:
            logger.error(f"Application startup failed: {e}")
            raise
    
    return startup_handler


def create_stop_app_handler() -> Callable:
    """
    Create application shutdown handler.
    
    Returns:
        Callable: Shutdown event handler function
    """
    def shutdown_handler() -> None:
        """Handle application shutdown."""
        logger.info("Shutting down CMS application...")
        
        try:
            # Close database connections
            engine.dispose()
            logger.info("Database connections closed")
            
            logger.info("CMS application shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
    
    return shutdown_handler