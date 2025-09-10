"""
Health check endpoints for monitoring application status.

Provides endpoints for:
- Basic application health
- Database connectivity
- System status and metrics
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import time
import logging

from db.session import get_db, get_db_info
from db.init_db import check_database_health
from core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", response_model=Dict[str, Any])
def health_check():
    """
    Basic health check endpoint.
    
    Returns basic application status without database checks.
    Used by Docker healthcheck and load balancers.
    
    Returns:
        dict: Basic health status
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": int(time.time())
    }


@router.get("/health/detailed", response_model=Dict[str, Any])
def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check including database connectivity.
    
    Performs comprehensive health checks including:
    - Database connection
    - Table existence
    - Connection pool status
    
    Args:
        db: Database session dependency
        
    Returns:
        dict: Detailed health status
        
    Raises:
        HTTPException: If health check fails
    """
    try:
        # Get database health
        db_health = check_database_health()
        
        # Get connection pool info
        pool_info = get_db_info()
        
        # Test database query
        start_time = time.time()
        db.execute("SELECT 1")
        db_response_time = (time.time() - start_time) * 1000  # ms
        
        health_data = {
            "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "timestamp": int(time.time()),
            "checks": {
                "database": db_health,
                "database_response_time_ms": round(db_response_time, 2)
            },
            "info": {
                "connection_pool": pool_info,
                "environment": getattr(settings, 'ENVIRONMENT', 'unknown')
            }
        }
        
        if health_data["status"] == "unhealthy":
            raise HTTPException(status_code=503, detail=health_data)
            
        return health_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        error_response = {
            "status": "unhealthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "timestamp": int(time.time()),
            "error": str(e)
        }
        raise HTTPException(status_code=503, detail=error_response)


@router.get("/health/database", response_model=Dict[str, Any])
def database_health_check(db: Session = Depends(get_db)):
    """
    Database-specific health check.
    
    Focuses on database connectivity and performance.
    
    Args:
        db: Database session dependency
        
    Returns:
        dict: Database health status
    """
    try:
        health = check_database_health()
        pool_info = get_db_info()
        
        # Test query performance
        start_time = time.time()
        db.execute("SELECT COUNT(*) FROM categories")
        query_time = (time.time() - start_time) * 1000
        
        return {
            "status": health["status"],
            "database_info": health.get("info", {}),
            "connection_pool": pool_info,
            "query_performance_ms": round(query_time, 2),
            "checks": health.get("checks", {}),
            "timestamp": int(time.time())
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": int(time.time())
            }
        )


@router.get("/health/ready", response_model=Dict[str, str])
def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe endpoint.
    
    Checks if the application is ready to receive traffic.
    
    Args:
        db: Database session dependency
        
    Returns:
        dict: Readiness status
    """
    try:
        # Quick database test
        db.execute("SELECT 1")
        
        return {
            "status": "ready",
            "timestamp": str(int(time.time()))
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "error": str(e),
                "timestamp": str(int(time.time()))
            }
        )


@router.get("/health/live", response_model=Dict[str, str])
def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    
    Checks if the application is alive and should not be restarted.
    
    Returns:
        dict: Liveness status
    """
    return {
        "status": "alive",
        "timestamp": str(int(time.time()))
    }