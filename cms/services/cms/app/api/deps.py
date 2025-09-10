"""
FastAPI Dependencies

This module provides dependency injection functions for FastAPI endpoints
including database sessions, authentication, and common utilities.
"""

import uuid
from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from db.session import get_db as get_database_session
from core.security import authenticate_user_placeholder, UserInfo


# Security scheme for JWT tokens
security_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """
    Database dependency for FastAPI endpoints.
    
    This is a re-export of the database session dependency from db.session
    to provide a consistent import path for all dependencies.
    
    Yields:
        Session: SQLAlchemy database session
    """
    yield from get_database_session()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> uuid.UUID:
    """
    Get current authenticated user ID.
    
    This dependency requires a valid JWT token and returns the user ID.
    Raises HTTPException if authentication fails.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        uuid.UUID: Current user's UUID
        
    Raises:
        HTTPException: 401 if authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verify token and get user info
    user_info = authenticate_user_placeholder(credentials.credentials)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user_info.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user_info.id


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Optional[uuid.UUID]:
    """
    Get current authenticated user ID (optional).
    
    This dependency accepts optional authentication and returns the user ID
    if a valid token is provided, or None if no token or invalid token.
    Does not raise exceptions for missing/invalid authentication.
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        
    Returns:
        Optional[uuid.UUID]: Current user's UUID or None if not authenticated
    """
    if not credentials:
        return None
    
    try:
        # Verify token and get user info
        user_info = authenticate_user_placeholder(credentials.credentials)
        
        if not user_info or not user_info.is_active:
            return None
            
        return user_info.id
        
    except Exception:
        # Silently handle any authentication errors for optional auth
        return None


async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> UserInfo:
    """
    Get complete current user information.
    
    This dependency requires a valid JWT token and returns full user info
    including permissions. Raises HTTPException if authentication fails.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        UserInfo: Complete user information with permissions
        
    Raises:
        HTTPException: 401 if authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verify token and get user info
    user_info = authenticate_user_placeholder(credentials.credentials)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user_info.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user_info


async def get_optional_current_user_info(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Optional[UserInfo]:
    """
    Get complete current user information (optional).
    
    This dependency accepts optional authentication and returns full user info
    if a valid token is provided, or None if no token or invalid token.
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        
    Returns:
        Optional[UserInfo]: Complete user information or None if not authenticated
    """
    if not credentials:
        return None
    
    try:
        # Verify token and get user info
        user_info = authenticate_user_placeholder(credentials.credentials)
        
        if not user_info or not user_info.is_active:
            return None
            
        return user_info
        
    except Exception:
        # Silently handle any authentication errors for optional auth
        return None


def require_permission(permission: str):
    """
    Dependency factory for requiring specific permissions.
    
    Creates a dependency that checks if the current user has the specified permission.
    
    Args:
        permission: Required permission string
        
    Returns:
        Dependency function that validates permission
        
    Example:
        @router.post("/admin-only")
        def admin_endpoint(
            user: UserInfo = Depends(require_permission("admin"))
        ):
            return {"message": "Admin access granted"}
    """
    async def permission_dependency(
        user_info: UserInfo = Depends(get_current_user_info)
    ) -> UserInfo:
        if permission not in user_info.permissions and "admin" not in user_info.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return user_info
    
    return permission_dependency


def require_any_permission(permissions: list):
    """
    Dependency factory for requiring any of multiple permissions.
    
    Creates a dependency that checks if the current user has any of the specified permissions.
    
    Args:
        permissions: List of acceptable permission strings
        
    Returns:
        Dependency function that validates permissions
        
    Example:
        @router.post("/content")
        def create_content(
            user: UserInfo = Depends(require_any_permission(["create_content", "admin"]))
        ):
            return {"message": "Content creation access granted"}
    """
    async def permission_dependency(
        user_info: UserInfo = Depends(get_current_user_info)
    ) -> UserInfo:
        user_permissions = set(user_info.permissions)
        required_permissions = set(permissions)
        
        if not user_permissions.intersection(required_permissions) and "admin" not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these permissions required: {', '.join(permissions)}"
            )
        return user_info
    
    return permission_dependency


# Convenience dependency aliases for common use cases

# Content management permissions
require_content_create = require_permission("create_content")
require_content_edit = require_any_permission(["edit_content", "edit_any_content"])
require_content_delete = require_any_permission(["delete_content", "delete_any_content"])
require_content_publish = require_any_permission(["publish_content", "publish_any_content"])

# Series management permissions  
require_series_create = require_permission("create_series")
require_series_edit = require_any_permission(["edit_series", "edit_any_series"])
require_series_delete = require_any_permission(["delete_series", "delete_any_series"])
require_series_publish = require_any_permission(["publish_series", "publish_any_series"])

# Analytics permissions
require_analytics_view = require_any_permission(["view_analytics", "view_any_analytics"])
require_stats_view = require_any_permission(["view_stats", "view_all_stats"])

# Admin permissions
require_admin = require_permission("admin")


# Legacy compatibility functions (for existing code)

def get_current_user_legacy() -> dict:
    """
    Legacy compatibility function for existing endpoints.
    
    Returns a dictionary with user info for backward compatibility
    with existing code that expects dict format.
    
    Returns:
        dict: User information dictionary
    """
    # This is a simplified version for backward compatibility
    # In production, you'd want to properly implement this
    return {
        "id": uuid.uuid4(),
        "email": "user@example.com",
        "is_active": True
    }