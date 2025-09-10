"""
Security utilities for authentication and authorization.

This module provides JWT token handling, password hashing, and user authentication
functions for the CMS application.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from pydantic import BaseModel

from core.config import settings


class TokenData(BaseModel):
    """Token data structure"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    permissions: Optional[list] = None


class UserInfo(BaseModel):
    """User information structure"""
    id: uuid.UUID
    email: str
    is_active: bool = True
    permissions: list = []


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Data to encode in token
        expires_delta: Token expiration time
        
    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify JWT token and extract user data.
    
    Args:
        token: JWT token to verify
        
    Returns:
        TokenData: Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        permissions: list = payload.get("permissions", [])
        
        if user_id is None:
            return None
            
        return TokenData(user_id=user_id, email=email, permissions=permissions)
        
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def get_user_id_from_token(token: str) -> Optional[uuid.UUID]:
    """
    Extract user ID from JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        UUID: User ID or None if invalid
    """
    token_data = verify_token(token)
    if token_data and token_data.user_id:
        try:
            return uuid.UUID(token_data.user_id)
        except ValueError:
            return None
    return None


# Placeholder authentication functions for development
# In production, these should integrate with your actual user management system

def authenticate_user_placeholder(token: str) -> Optional[UserInfo]:
    """
    Placeholder authentication function for development.
    
    In production, this should:
    1. Validate the JWT token
    2. Query the user from database
    3. Check if user is active
    4. Return user info with permissions
    
    Args:
        token: JWT token
        
    Returns:
        UserInfo: User information or None if invalid
    """
    # For development/demo purposes, return a mock user
    # Replace this with real authentication logic
    
    if not token or token == "invalid":
        return None
    
    # Mock user data - replace with real database lookup
    return UserInfo(
        id=uuid.uuid4(),
        email="user@example.com",
        is_active=True,
        permissions=["read", "write", "create_series", "edit_content"]
    )


def get_user_permissions(user_id: uuid.UUID) -> list:
    """
    Get user permissions from database.
    
    In production, this should query the user's roles and permissions
    from the database.
    
    Args:
        user_id: User UUID
        
    Returns:
        list: List of permission strings
    """
    # Placeholder implementation
    # Replace with actual permission lookup from database
    return [
        "read", "write", "create_content", "edit_content", "delete_content",
        "create_series", "edit_series", "delete_series", "publish_content",
        "publish_series", "view_analytics"
    ]


def check_user_permission(user_id: uuid.UUID, permission: str) -> bool:
    """
    Check if user has specific permission.
    
    Args:
        user_id: User UUID
        permission: Permission string to check
        
    Returns:
        bool: True if user has permission
    """
    user_permissions = get_user_permissions(user_id)
    return permission in user_permissions or "admin" in user_permissions