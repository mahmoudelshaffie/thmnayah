"""
Core module for CMS application.

This module provides core functionality including configuration, dependencies,
security, and common utilities used across the application.
"""

from .config import settings
from .security import (
    create_access_token, verify_token, verify_password, get_password_hash,
    get_user_id_from_token, UserInfo, TokenData
)

__all__ = [
    # Configuration
    "settings",
    
    # Dependencies
    "get_db",
    "get_current_user", 
    "get_optional_current_user",
    "get_current_user_info",
    "get_optional_current_user_info",
    
    # Permission dependencies
    "require_permission",
    "require_any_permission",
    "require_content_create",
    "require_content_edit", 
    "require_content_delete",
    "require_series_create",
    "require_series_edit",
    "require_series_delete",
    "require_analytics_view",
    "require_admin",
    
    # Security utilities
    "create_access_token",
    "verify_token",
    "verify_password",
    "get_password_hash",
    "get_user_id_from_token",
    "UserInfo",
    "TokenData"
]