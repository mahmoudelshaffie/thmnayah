"""
Thmnayah CMS API v1 Router Aggregation

This module aggregates all API v1 routers for the Thmnayah Content Management System.
It provides a centralized entry point for all API endpoints with proper organization and documentation.

API Design Principles:
1. RESTful design with proper HTTP methods and status codes
2. Comprehensive OpenAPI documentation for each endpoint
3. Multilingual support (Arabic/English) throughout the API
4. User story driven development with clear business context
5. Extensible architecture supporting future AI enhancements
6. General content focus with appropriate categorization
7. Role-based access control for different user types
8. Background task integration for async operations

Router Organization:
- /content: Content management (CRUD, search, workflow, export)
- /series: Series and episode management with subscriptions
- /categories: Hierarchical content categorization
- /users: User profile and preference management
- /auth: Authentication, authorization, and security
"""

from fastapi import APIRouter
from api.v1.endpoints.content import router as content_router
from api.v1.endpoints.series import router as series_router
from api.v1.endpoints.categories import router as categories_router
from api.v1.endpoints.health import router as health_router
from api.v1.endpoints.users import router as users_router
from api.v1.endpoints.auth import router as auth_router

# Create the main API v1 router
api_router = APIRouter(prefix="/api/v1")

# Include all sub-routers with appropriate prefixes and tags
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
    }
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["User Management"],
    dependencies=[],  # Add auth dependency in production
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "User not found"},
    }
)

api_router.include_router(
    content_router,
    prefix="/content",
    tags=["Content Management"],
    dependencies=[],  # Add auth dependency in production
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Content access forbidden"},
        404: {"description": "Content not found"},
    }
)

api_router.include_router(
    series_router,
    prefix="/series",
    tags=["Series Management"],
    dependencies=[],  # Add auth dependency in production
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Series not found"},
    }
)

api_router.include_router(
    health_router,
    tags=["Health & Monitoring"],
    responses={
        503: {"description": "Service unavailable"},
    }
)

api_router.include_router(
    categories_router,
    prefix="/categories",
    tags=["Category Management"], 
    dependencies=[],  # Add auth dependency in production
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Category not found"},
    }
)

# Export the main router for use in the FastAPI application
__all__ = ["api_router"]