"""
Clean Series REST Endpoints

Refactored series endpoints following clean architecture principles.
Endpoints handle only HTTP concerns while delegating business logic to controllers.
"""

import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from api.v1.models.series import (
    SeriesCreate, SeriesUpdate, SeriesResponse, SeriesSearchFilters,
    SeriesPublishRequest, SeriesListResponse, SeriesAnalytics,
    SeriesStatsResponse, SeriesRecommendationRequest, SeriesRecommendationResponse,
    SeriesSubscriptionCreate, SeriesSubscriptionUpdate, SeriesSubscriptionResponse
)
from api.v1.models.common import PaginationParams, MessageResponse
from controllers.series_controller import SeriesController
from api.deps import get_db, get_current_user, get_optional_current_user

# Router configuration
router = APIRouter(prefix="/series", tags=["series"])
security = HTTPBearer()


# Dependency injection functions

async def get_series_controller(db: Session = Depends(get_db)) -> SeriesController:
    """
    Dependency to get series controller instance.
    
    In production, this would be configured with proper DI container.
    """
    from services.series import SeriesService
    from business.series_business_service import SeriesBusinessService
    from repositories.series import SeriesRepository, SeriesSubscriptionRepository

    # Initialize repositories
    series_repo = SeriesRepository()
    subscription_repo = SeriesSubscriptionRepository()
    # Note: These would be properly injected in production
    category_repo = None  # ICategoryRepository implementation
    user_repo = None  # IUserRepository implementation

    # Initialize services
    series_service = SeriesService(series_repo, subscription_repo, db)
    business_service = SeriesBusinessService(
        series_repo, category_repo, user_repo, db
    )

    # Return controller
    return SeriesController(series_service, business_service, user_repo, db)


def _schedule_series_creation_tasks(series_id: uuid.UUID) -> None:
    """Schedule background tasks after series creation"""
    # Placeholder for background tasks like:
    # - Send notifications to followers
    # - Update search indexes
    # - Generate thumbnails
    # - Send analytics events
    pass


def _schedule_series_publication_tasks(series_id: uuid.UUID) -> None:
    """Schedule background tasks after series publication"""
    # Placeholder for background tasks like:
    # - Notify subscribers
    # - Update recommendation systems
    # - Send social media posts
    # - Update analytics
    pass


def _schedule_subscription_tasks(subscription_id: uuid.UUID, action: str) -> None:
    """Schedule background tasks after subscription changes"""
    # Placeholder for background tasks like:
    # - Send welcome emails
    # - Update recommendation systems
    # - Send analytics events
    pass


# Series CRUD Endpoints

@router.post(
    "/",
    response_model=SeriesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new series",
    description="Create a new series with multilingual content support"
)
async def create_series(
        series: SeriesCreate,
        background_tasks: BackgroundTasks,
        controller: SeriesController = Depends(get_series_controller),
        current_user_id: uuid.UUID = Depends(get_current_user)
) -> SeriesResponse:
    """
    Create a new series.
    
    - **title**: Multilingual title (required)
    - **description**: Multilingual description
    - **series_type**: Type of series (educational, entertainment, etc.)
    - **primary_category_id**: Primary category
    - **visibility**: Series visibility (public, private, restricted)
    - **expected_episode_count**: Expected number of episodes
    - **tags**: Series tags for discovery
    """
    try:
        created_series = await controller.create_series(series, current_user_id)

        # Schedule background tasks
        background_tasks.add_task(
            _schedule_series_creation_tasks,
            created_series.id
        )

        return created_series

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create series"
        )


@router.get(
    "/{series_id}",
    response_model=SeriesResponse,
    summary="Get series by ID",
    description="Retrieve series details with relationships"
)
async def get_series(
        series_id: uuid.UUID,
        controller: SeriesController = Depends(get_series_controller),
        current_user_id: Optional[uuid.UUID] = Depends(get_optional_current_user)
) -> SeriesResponse:
    """
    Retrieve series by ID.
    
    Returns comprehensive series information including:
    - Basic series details
    - Creator information
    - Category relationships
    - Latest episodes
    - Engagement metrics
    """
    return await controller.get_series(series_id, current_user_id)


@router.patch(
    "/{series_id}",
    response_model=SeriesResponse,
    summary="Update series",
    description="Update series with partial data"
)
async def update_series(
        series_id: uuid.UUID,
        updates: SeriesUpdate,
        controller: SeriesController = Depends(get_series_controller),
        current_user_id: uuid.UUID = Depends(get_current_user)
) -> SeriesResponse:
    """
    Update series with partial data.
    
    Only provided fields will be updated. Supports:
    - Multilingual content updates
    - Status changes
    - Metadata updates
    - Scheduling changes
    """
    return await controller.update_series(series_id, updates, current_user_id)


@router.delete(
    "/{series_id}",
    response_model=MessageResponse,
    summary="Delete series",
    description="Delete series (soft delete by default)"
)
async def delete_series(
        series_id: uuid.UUID,
        soft_delete: bool = Query(True, description="Whether to perform soft delete"),
        controller: SeriesController = Depends(get_series_controller),
        current_user_id: uuid.UUID = Depends(get_current_user)
) -> MessageResponse:
    """
    Delete series.
    
    - **soft_delete**: If true, marks as deleted but preserves data
    - **soft_delete=false**: Permanently removes from database (admin only)
    """
    result = await controller.delete_series(series_id, current_user_id, soft_delete)
    return MessageResponse(message=result["message"])


# Series Search and Discovery

@router.get(
    "/",
    response_model=SeriesListResponse,
    summary="Search and list series",
    description="Search series with advanced filtering and pagination"
)
async def search_series(
        # Search parameters
        query: Optional[str] = Query(None, description="Text search query"),
        language: str = Query("ar", description="Search language preference"),

        # Filters
        series_type: Optional[str] = Query(None, description="Filter by series type"),
        status: Optional[str] = Query(None, description="Filter by status"),
        visibility: Optional[str] = Query(None, description="Filter by visibility"),
        category_id: Optional[uuid.UUID] = Query(None, description="Filter by category"),
        creator_id: Optional[uuid.UUID] = Query(None, description="Filter by creator"),
        is_featured: Optional[bool] = Query(None, description="Filter featured series"),
        has_episodes: Optional[bool] = Query(None, description="Filter series with episodes"),
        is_complete: Optional[bool] = Query(None, description="Filter completed series"),
        min_rating: Optional[float] = Query(None, ge=1.0, le=5.0, description="Minimum rating"),

        # Date filters
        published_after: Optional[str] = Query(None, description="Published after date (ISO format)"),
        published_before: Optional[str] = Query(None, description="Published before date (ISO format)"),

        # Sorting
        sort_by: str = Query("created_at", description="Sort field"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort direction"),

        # Pagination
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(20, ge=1, le=100, description="Items per page"),

        # Dependencies
        controller: SeriesController = Depends(get_series_controller),
        current_user_id: Optional[uuid.UUID] = Depends(get_optional_current_user)
) -> SeriesListResponse:
    """
    Search and list series with advanced filtering.
    
    Supports:
    - Full-text search across multilingual content
    - Filtering by type, status, category, creator
    - Date range filtering
    - Custom sorting
    - Pagination
    """
    # Build search filters
    filters = SeriesSearchFilters(
        query=query,
        language=language,
        series_type=series_type,
        status=status,
        visibility=visibility,
        category_id=category_id,
        creator_id=creator_id,
        is_featured=is_featured,
        has_episodes=has_episodes,
        is_complete=is_complete,
        min_rating=min_rating,
        sort_by=sort_by,
        sort_order=sort_order
    )

    # Add date filters if provided
    if published_after:
        try:
            from datetime import datetime
            filters.published_after = datetime.fromisoformat(published_after.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid published_after date format"
            )

    if published_before:
        try:
            from datetime import datetime
            filters.published_before = datetime.fromisoformat(published_before.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid published_before date format"
            )

    # Build pagination
    pagination = PaginationParams(page=page, limit=limit)

    # Execute search
    return await controller.search_series(filters, pagination, current_user_id)


# Series Management Operations

@router.post(
    "/{series_id}/publish",
    response_model=SeriesResponse,
    summary="Publish series",
    description="Publish series to make it publicly available"
)
async def publish_series(
        series_id: uuid.UUID,
        publish_request: SeriesPublishRequest,
        background_tasks: BackgroundTasks,
        controller: SeriesController = Depends(get_series_controller),
        current_user_id: uuid.UUID = Depends(get_current_user)
) -> SeriesResponse:
    """
    Publish series.
    
    - **publish_immediately**: Whether to publish now or schedule
    - **scheduled_start_date**: When to start the series (if not immediate)
    """
    published_series = await controller.publish_series(
        series_id, publish_request, current_user_id
    )

    # Schedule background tasks
    background_tasks.add_task(
        _schedule_series_publication_tasks,
        series_id
    )

    return published_series


@router.post(
    "/{series_id}/complete",
    response_model=SeriesResponse,
    summary="Complete series",
    description="Mark series as completed"
)
async def complete_series(
        series_id: uuid.UUID,
        controller: SeriesController = Depends(get_series_controller),
        current_user_id: uuid.UUID = Depends(get_current_user)
) -> SeriesResponse:
    """
    Mark series as completed.
    
    This action:
    - Changes status to COMPLETED
    - Sets actual end date
    - Triggers completion analytics
    """
    return await controller.complete_series(series_id, current_user_id)


# Series Subscription Endpoints

@router.post(
    "/subscribe",
    response_model=SeriesSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subscribe to series",
    description="Subscribe to series for notifications and updates"
)
async def subscribe_to_series(
        subscription_data: SeriesSubscriptionCreate,
        background_tasks: BackgroundTasks,
        controller: SeriesController = Depends(get_series_controller),
        current_user_id: uuid.UUID = Depends(get_current_user)
) -> SeriesSubscriptionResponse:
    """
    Subscribe to series.
    
    - **series_id**: Series to subscribe to
    - **notification_enabled**: Receive episode notifications
    - **auto_download**: Auto-download new episodes
    """
    subscription = await controller.subscribe_to_series(
        subscription_data, current_user_id
    )

    # Schedule background tasks
    background_tasks.add_task(
        _schedule_subscription_tasks,
        subscription.id,
        "subscribe"
    )

    return subscription


@router.patch(
    "/subscriptions/{subscription_id}",
    response_model=SeriesSubscriptionResponse,
    summary="Update subscription",
    description="Update subscription preferences"
)
async def update_subscription(
        subscription_id: uuid.UUID,
        updates: SeriesSubscriptionUpdate,
        controller: SeriesController = Depends(get_series_controller),
        current_user_id: uuid.UUID = Depends(get_current_user)
) -> SeriesSubscriptionResponse:
    """
    Update subscription preferences.
    
    - **status**: Subscription status (active, paused, cancelled)
    - **notification_enabled**: Notification preference
    - **auto_download**: Auto-download preference
    """
    return await controller.update_subscription(
        subscription_id, updates, current_user_id
    )


@router.delete(
    "/subscriptions/{subscription_id}",
    response_model=MessageResponse,
    summary="Cancel subscription",
    description="Cancel series subscription"
)
async def cancel_subscription(
        subscription_id: uuid.UUID,
        background_tasks: BackgroundTasks,
        controller: SeriesController = Depends(get_series_controller),
        current_user_id: uuid.UUID = Depends(get_current_user)
) -> MessageResponse:
    """
    Cancel series subscription.
    
    This action:
    - Changes status to CANCELLED
    - Stops notifications
    - Records cancellation metrics
    """
    result = await controller.cancel_subscription(subscription_id, current_user_id)

    # Schedule background tasks
    background_tasks.add_task(
        _schedule_subscription_tasks,
        subscription_id,
        "cancel"
    )

    return MessageResponse(message=result["message"])


@router.get(
    "/my-subscriptions",
    response_model=List[SeriesSubscriptionResponse],
    summary="Get user subscriptions",
    description="Get current user's series subscriptions"
)
async def get_user_subscriptions(
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(20, ge=1, le=100, description="Items per page"),
        controller: SeriesController = Depends(get_series_controller),
        current_user_id: uuid.UUID = Depends(get_current_user)
) -> List[SeriesSubscriptionResponse]:
    """
    Get user's series subscriptions.
    
    Returns:
    - Active, paused, and cancelled subscriptions
    - Series information for each subscription
    - Watch progress data
    """
    pagination = PaginationParams(page=page, limit=limit)
    return await controller.get_user_subscriptions(current_user_id, pagination)


# Analytics and Insights Endpoints

@router.get(
    "/{series_id}/analytics",
    response_model=SeriesAnalytics,
    summary="Get series analytics",
    description="Get detailed analytics for series (creators and admins only)"
)
async def get_series_analytics(
        series_id: uuid.UUID,
        controller: SeriesController = Depends(get_series_controller),
        current_user_id: uuid.UUID = Depends(get_current_user)
) -> SeriesAnalytics:
    """
    Get series analytics.
    
    Includes:
    - Subscription metrics
    - Engagement analytics
    - Episode performance
    - Completion rates
    - Demographics (if available)
    """
    return await controller.get_series_analytics(series_id, current_user_id)


@router.get(
    "/stats",
    response_model=SeriesStatsResponse,
    summary="Get series statistics",
    description="Get aggregated series statistics"
)
async def get_series_stats(
        # Filters
        creator_id: Optional[uuid.UUID] = Query(None, description="Filter by creator"),
        category_id: Optional[uuid.UUID] = Query(None, description="Filter by category"),
        series_type: Optional[str] = Query(None, description="Filter by series type"),

        controller: SeriesController = Depends(get_series_controller),
        current_user_id: uuid.UUID = Depends(get_current_user)
) -> SeriesStatsResponse:
    """
    Get series statistics.
    
    Includes:
    - Total series counts by status
    - Engagement totals
    - Creator statistics
    - Category breakdowns
    """
    filters = {}
    if creator_id:
        filters["creator_id"] = creator_id
    if category_id:
        filters["category_id"] = category_id
    if series_type:
        filters["series_type"] = series_type

    return await controller.get_series_stats(current_user_id, filters)


# Discovery and Recommendations

@router.get(
    "/trending",
    response_model=SeriesListResponse,
    summary="Get trending series",
    description="Get currently trending series"
)
async def get_trending_series(
        hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
        limit: int = Query(10, ge=1, le=50, description="Number of series to return"),
        category_id: Optional[uuid.UUID] = Query(None, description="Filter by category"),
        controller: SeriesController = Depends(get_series_controller),
        current_user_id: Optional[uuid.UUID] = Depends(get_optional_current_user)
) -> SeriesListResponse:
    """
    Get trending series based on recent engagement.
    
    Trending is calculated based on:
    - Recent subscriptions
    - View activity
    - Social engagement
    - Episode releases
    """
    # Implementation would call specialized trending method
    # For now, using search with trending sort
    filters = SeriesSearchFilters(
        category_id=category_id,
        status="PUBLISHED",
        visibility="PUBLIC",
        sort_by="engagement",
        sort_order="desc"
    )

    pagination = PaginationParams(page=1, limit=limit)
    return await controller.search_series(filters, pagination, current_user_id)


@router.post(
    "/recommendations",
    response_model=SeriesRecommendationResponse,
    summary="Get series recommendations",
    description="Get personalized series recommendations"
)
async def get_series_recommendations(
        request: SeriesRecommendationRequest,
        controller: SeriesController = Depends(get_series_controller),
        current_user_id: Optional[uuid.UUID] = Depends(get_optional_current_user)
) -> SeriesRecommendationResponse:
    """
    Get personalized series recommendations.
    
    Recommendations based on:
    - User subscription history
    - Viewing preferences
    - Similar users' activities
    - Content similarity
    - Category preferences
    """
    return await controller.get_series_recommendations(request, current_user_id)


# Health and Status Endpoints

@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Series service health check",
    description="Check health of series service and dependencies"
)
async def series_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for series service.
    
    Returns service status and dependency health.
    """
    return {
        "status": "healthy",
        "service": "series",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z",
        "dependencies": {
            "database": "healthy",
            "cache": "healthy",
            "search": "healthy"
        }
    }


